"""Lightweight reproducibility and output-contract checks."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    clean = pd.read_csv(ROOT / "data" / "processed" / "drug_involved_counts_clean.csv")
    annual = pd.read_csv(ROOT / "data" / "processed" / "annual_december_snapshots.csv")
    national = pd.read_csv(ROOT / "outputs" / "tables" / "national_latest_yoy_change.csv")
    regional = pd.read_csv(ROOT / "outputs" / "tables" / "regional_latest_yoy_change.csv")
    qa = pd.read_csv(ROOT / "outputs" / "tables" / "qa_checks.csv")
    results = json.loads((ROOT / "outputs" / "tables" / "key_results.json").read_text(encoding="utf-8"))

    assert len(clean) == 11088
    assert clean[["jurisdiction_occurrence", "drug_involved", "month_ending_date"]].duplicated().sum() == 0
    assert clean["jurisdiction_occurrence"].nunique() == 11
    assert clean["drug_involved"].nunique() == 12
    assert annual["month_ending_date"].str.endswith("12-31").all()
    assert len(national) == 12
    assert len(regional) == 120
    assert qa["passed"].astype(str).str.lower().eq("true").all()
    assert results["latest_period_ending"] == "2025-12-31"
    assert (ROOT / "outputs" / "figures" / "overdose_drug_signal_dashboard.png").stat().st_size > 100_000
    print("All output and QA assertions passed.")


if __name__ == "__main__":
    main()
