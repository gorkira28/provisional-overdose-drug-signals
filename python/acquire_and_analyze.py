"""Acquire and analyze CDC provisional drug-involved overdose death counts.

The workflow intentionally uses 12-month ending December snapshots for year-over-year
comparisons so adjacent analytic periods do not overlap. Counts are descriptive and
must not be interpreted as population risk or mutually exclusive drug categories.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"

DATASET_ID = "8hzs-zshh"
SOURCE_URL = f"https://data.cdc.gov/resource/{DATASET_ID}.csv?$limit=50000"
METADATA_URL = f"https://data.cdc.gov/api/views/{DATASET_ID}"
SNAPSHOT_DATE = "2026-10-20"
CORE_DRUGS = ["Fentanyl", "Cocaine", "Methamphetamine", "Xylazine", "Ketamine"]


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, TABLE_DIR, FIGURE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acquire() -> tuple[Path, dict]:
    ensure_directories()
    raw_path = RAW_DIR / f"cdc_drug_involved_counts_{SNAPSHOT_DATE}.csv"
    metadata_path = RAW_DIR / f"cdc_dataset_metadata_{SNAPSHOT_DATE}.json"

    response = requests.get(SOURCE_URL, timeout=90)
    response.raise_for_status()
    raw_path.write_bytes(response.content)

    metadata_response = requests.get(METADATA_URL, timeout=90)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    manifest = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "dataset_id": DATASET_ID,
        "source_url": SOURCE_URL,
        "metadata_url": METADATA_URL,
        "files": [
            {
                "path": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
                "bytes": raw_path.stat().st_size,
                "sha256": sha256(raw_path),
            },
            {
                "path": str(metadata_path.relative_to(ROOT)).replace("\\", "/"),
                "bytes": metadata_path.stat().st_size,
                "sha256": sha256(metadata_path),
            },
        ],
    }
    (RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return raw_path, metadata


def wilson_interval(successes: int, total: int, z: float = 1.959964) -> tuple[float, float]:
    if total == 0:
        return (math.nan, math.nan)
    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    half = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return center - half, center + half


def clean(raw_path: Path) -> pd.DataFrame:
    df = pd.read_csv(raw_path, dtype=str)
    expected = {
        "data_as_of",
        "death_year",
        "death_month",
        "jurisdiction_occurrence",
        "drug_involved",
        "time_period",
        "month_ending_date",
        "drug_overdose_deaths",
        "footnote",
    }
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["data_as_of"] = pd.to_datetime(df["data_as_of"], errors="raise")
    df["month_ending_date"] = pd.to_datetime(df["month_ending_date"], errors="raise")
    df["death_year"] = pd.to_numeric(df["death_year"], errors="raise").astype("int16")
    df["drug_overdose_deaths"] = pd.to_numeric(df["drug_overdose_deaths"], errors="coerce")
    df["is_suppressed_or_missing"] = df["drug_overdose_deaths"].isna()
    df["is_united_states"] = df["jurisdiction_occurrence"].eq("United States")
    df["is_hhs_region"] = df["jurisdiction_occurrence"].str.startswith("Region ")
    df["is_december_snapshot"] = df["month_ending_date"].dt.month.eq(12)
    df = df.sort_values(["drug_involved", "jurisdiction_occurrence", "month_ending_date"]).reset_index(drop=True)
    return df


def annual_percent_change(annual_us: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for drug, group in annual_us.groupby("drug_involved", sort=True):
        group = group.dropna(subset=["drug_overdose_deaths"]).copy()
        group = group[group["drug_overdose_deaths"] > 0]
        if len(group) < 4:
            continue
        x = group["death_year"].to_numpy(dtype=float)
        y = np.log(group["drug_overdose_deaths"].to_numpy(dtype=float))
        fit = stats.linregress(x, y)
        dfree = len(group) - 2
        crit = stats.t.ppf(0.975, dfree)
        lo = fit.slope - crit * fit.stderr
        hi = fit.slope + crit * fit.stderr
        rows.append(
            {
                "drug_involved": drug,
                "first_year": int(group["death_year"].min()),
                "last_year": int(group["death_year"].max()),
                "annual_snapshots": len(group),
                "model_apc_percent": 100 * (math.exp(fit.slope) - 1),
                "model_apc_ci_low": 100 * (math.exp(lo) - 1),
                "model_apc_ci_high": 100 * (math.exp(hi) - 1),
                "r_squared": fit.rvalue**2,
                "p_value": fit.pvalue,
            }
        )
    return pd.DataFrame(rows).sort_values("model_apc_percent", ascending=False)


def analyze(df: pd.DataFrame) -> dict:
    ensure_directories()
    processed_path = PROCESSED_DIR / "drug_involved_counts_clean.csv"
    df.to_csv(processed_path, index=False, date_format="%Y-%m-%d")

    key = ["jurisdiction_occurrence", "drug_involved", "month_ending_date"]
    latest_date = df["month_ending_date"].max()
    previous_date = latest_date - pd.DateOffset(years=1)
    annual = df[df["is_december_snapshot"]].copy()
    annual.to_csv(PROCESSED_DIR / "annual_december_snapshots.csv", index=False, date_format="%Y-%m-%d")

    us = df[df["is_united_states"]].copy()
    current = us[us["month_ending_date"].eq(latest_date)][["drug_involved", "drug_overdose_deaths"]].rename(
        columns={"drug_overdose_deaths": "latest_count"}
    )
    previous = us[us["month_ending_date"].eq(previous_date)][["drug_involved", "drug_overdose_deaths"]].rename(
        columns={"drug_overdose_deaths": "previous_count"}
    )
    national_change = current.merge(previous, on="drug_involved", how="outer")
    national_change["absolute_change"] = national_change["latest_count"] - national_change["previous_count"]
    national_change["yoy_percent_change"] = 100 * national_change["absolute_change"] / national_change["previous_count"]
    national_change = national_change.sort_values("latest_count", ascending=False)
    national_change.to_csv(TABLE_DIR / "national_latest_yoy_change.csv", index=False, float_format="%.3f")

    regions = df[df["is_hhs_region"] & df["month_ending_date"].isin([previous_date, latest_date])].copy()
    regional = regions.pivot_table(
        index=["jurisdiction_occurrence", "drug_involved"],
        columns="month_ending_date",
        values="drug_overdose_deaths",
        aggfunc="first",
        dropna=False,
    ).reset_index()
    regional.columns = [
        "jurisdiction_occurrence",
        "drug_involved",
        "previous_count",
        "latest_count",
    ]
    regional["absolute_change"] = regional["latest_count"] - regional["previous_count"]
    regional["yoy_percent_change"] = 100 * regional["absolute_change"] / regional["previous_count"]
    regional.to_csv(TABLE_DIR / "regional_latest_yoy_change.csv", index=False, float_format="%.3f")

    annual_us = annual[annual["is_united_states"]].copy()
    trend_model = annual_percent_change(annual_us)
    trend_model.to_csv(TABLE_DIR / "national_loglinear_trends.csv", index=False, float_format="%.6f")

    latest_regions = df[df["is_hhs_region"] & df["month_ending_date"].eq(latest_date)].copy()
    regional_sum = latest_regions.groupby("drug_involved", as_index=False)["drug_overdose_deaths"].sum(min_count=1)
    regional_sum = regional_sum.rename(columns={"drug_overdose_deaths": "sum_hhs_regions"})
    reconciliation = current.merge(regional_sum, on="drug_involved", how="left")
    reconciliation["difference_us_minus_regions"] = reconciliation["latest_count"] - reconciliation["sum_hhs_regions"]
    reconciliation.to_csv(TABLE_DIR / "us_region_reconciliation.csv", index=False, float_format="%.3f")

    duplicate_count = int(df.duplicated(key).sum())
    expected_months = pd.period_range(df["month_ending_date"].min(), df["month_ending_date"].max(), freq="M").size
    observed_months = df["month_ending_date"].dt.to_period("M").nunique()
    qa = pd.DataFrame(
        [
            ["row_count", len(df), 11088, len(df) == 11088],
            ["unique_grain", duplicate_count, 0, duplicate_count == 0],
            ["jurisdictions", df["jurisdiction_occurrence"].nunique(), 11, df["jurisdiction_occurrence"].nunique() == 11],
            ["drug_categories", df["drug_involved"].nunique(), 12, df["drug_involved"].nunique() == 12],
            ["complete_month_sequence", observed_months, expected_months, observed_months == expected_months],
            ["one_data_as_of_date", df["data_as_of"].nunique(), 1, df["data_as_of"].nunique() == 1],
            ["nonnegative_counts", int((df["drug_overdose_deaths"].dropna() >= 0).all()), 1, bool((df["drug_overdose_deaths"].dropna() >= 0).all())],
        ],
        columns=["check", "observed", "expected", "passed"],
    )
    qa.to_csv(TABLE_DIR / "qa_checks.csv", index=False)
    if not qa["passed"].all():
        raise AssertionError("One or more QA checks failed")

    valid_latest = national_change.dropna(subset=["latest_count", "previous_count"]).copy()
    largest_count = valid_latest.loc[valid_latest["latest_count"].idxmax()]
    largest_decline = valid_latest.loc[valid_latest["yoy_percent_change"].idxmin()]
    largest_increase = valid_latest.loc[valid_latest["yoy_percent_change"].idxmax()]
    suppressed = int(df["is_suppressed_or_missing"].sum())
    total = len(df)
    low, high = wilson_interval(total - suppressed, total)
    summary = {
        "data_as_of": df["data_as_of"].max().date().isoformat(),
        "latest_period_ending": latest_date.date().isoformat(),
        "previous_period_ending": previous_date.date().isoformat(),
        "rows": total,
        "jurisdictions": int(df["jurisdiction_occurrence"].nunique()),
        "drug_categories": int(df["drug_involved"].nunique()),
        "available_counts": total - suppressed,
        "available_percent": 100 * (total - suppressed) / total,
        "available_percent_wilson_ci": [100 * low, 100 * high],
        "largest_latest_national_count_drug": str(largest_count["drug_involved"]),
        "largest_latest_national_count": int(largest_count["latest_count"]),
        "largest_yoy_decline_drug": str(largest_decline["drug_involved"]),
        "largest_yoy_decline_percent": float(largest_decline["yoy_percent_change"]),
        "largest_yoy_increase_drug": str(largest_increase["drug_involved"]),
        "largest_yoy_increase_percent": float(largest_increase["yoy_percent_change"]),
    }
    (TABLE_DIR / "key_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    make_dashboard(df, national_change, regional, latest_date, previous_date)
    return summary


def make_dashboard(
    df: pd.DataFrame,
    national_change: pd.DataFrame,
    regional: pd.DataFrame,
    latest_date: pd.Timestamp,
    previous_date: pd.Timestamp,
) -> None:
    selected = national_change[national_change["drug_involved"].isin(CORE_DRUGS)].copy()
    selected = selected.sort_values("yoy_percent_change")

    trend = df[
        df["is_united_states"]
        & df["drug_involved"].isin(CORE_DRUGS)
        & df["month_ending_date"].dt.month.eq(12)
    ].copy()
    region_heat = regional[regional["drug_involved"].isin(CORE_DRUGS)].pivot(
        index="drug_involved", columns="jurisdiction_occurrence", values="yoy_percent_change"
    )
    region_heat = region_heat.reindex(CORE_DRUGS)
    region_heat = region_heat[[f"Region {i}" for i in range(1, 11)]]

    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titlesize": 11, "axes.labelsize": 9})
    fig = plt.figure(figsize=(15, 9), facecolor="#f7f4ee")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.35, wspace=0.28)
    ax1 = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, :])

    colors = {
        "Fentanyl": "#0f6b6d",
        "Cocaine": "#d17a22",
        "Methamphetamine": "#6b5b95",
        "Xylazine": "#b23a48",
        "Ketamine": "#4d7c0f",
    }
    for drug in CORE_DRUGS:
        g = trend[trend["drug_involved"].eq(drug)]
        ax1.plot(g["death_year"], g["drug_overdose_deaths"], marker="o", linewidth=2.2, label=drug, color=colors[drug])
    ax1.set_title("National 12-month counts at December year-end")
    ax1.set_ylabel("Drug-involved overdose deaths")
    ax1.grid(axis="y", alpha=0.22)
    ax1.legend(frameon=False, fontsize=8, ncol=2)
    ax1.spines[["top", "right"]].set_visible(False)

    bar_colors = ["#b23a48" if value > 0 else "#0f6b6d" for value in selected["yoy_percent_change"]]
    ax2.barh(selected["drug_involved"], selected["yoy_percent_change"], color=bar_colors)
    ax2.axvline(0, color="#333333", linewidth=0.8)
    for i, value in enumerate(selected["yoy_percent_change"]):
        ax2.text(value + (1 if value >= 0 else -1), i, f"{value:.1f}%", va="center", ha="left" if value >= 0 else "right", fontsize=9)
    ax2.set_title(f"National year-over-year change\n{previous_date:%b %Y} to {latest_date:%b %Y}")
    ax2.set_xlabel("Percent change in count")
    ax2.set_xlim(min(-70, selected["yoy_percent_change"].min() - 8), max(22, selected["yoy_percent_change"].max() + 8))
    ax2.grid(axis="x", alpha=0.22)
    ax2.spines[["top", "right", "left"]].set_visible(False)

    vmax = np.nanpercentile(np.abs(region_heat.to_numpy(dtype=float)), 95)
    image = ax3.imshow(region_heat, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax3.set_xticks(range(10), [f"R{i}" for i in range(1, 11)])
    ax3.set_yticks(range(len(region_heat.index)), region_heat.index)
    ax3.set_title("HHS-region year-over-year change (%) — counts, not population risk")
    for row in range(region_heat.shape[0]):
        for col in range(region_heat.shape[1]):
            value = region_heat.iloc[row, col]
            label = "NA" if pd.isna(value) else f"{value:.0f}"
            ax3.text(col, row, label, ha="center", va="center", fontsize=8, color="#202020")
    cbar = fig.colorbar(image, ax=ax3, orientation="horizontal", fraction=0.06, pad=0.14)
    cbar.set_label("Year-over-year percent change")

    fig.suptitle("U.S. provisional drug-involved overdose mortality signals", x=0.06, y=0.98, ha="left", fontsize=20, fontweight="bold", color="#16324f")
    fig.text(0.06, 0.94, "CDC/NCHS 12-month ending counts · annual snapshots avoid overlapping analytic periods", fontsize=10, color="#4b5563")
    fig.text(0.06, 0.015, "Interpretation: categories can overlap; counts do not measure population risk; small baselines magnify % change. Provisional data may be revised.", fontsize=9, color="#4b5563")
    fig.savefig(FIGURE_DIR / "overdose_drug_signal_dashboard.png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    raw_path, metadata = acquire()
    df = clean(raw_path)
    summary = analyze(df)
    print(json.dumps({"dataset_name": metadata.get("name"), **summary}, indent=2))


if __name__ == "__main__":
    main()
