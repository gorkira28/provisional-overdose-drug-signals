# Run summary — October 20, 2026

## Project

**Provisional Drug-Involved Overdose Mortality Signals — SAS + Python**

## Key findings

- 11,088 CDC/NCHS rows covering 12 drug categories, 10 HHS regions, and the U.S. aggregate.
- Fentanyl remained the largest tracked category at 36,627 deaths in the 12-month period ending December 2025, down 22.9% year over year.
- Xylazine had the steepest national decline (−59.4%).
- Ketamine had the largest national percentage increase (+16.8%) but a much smaller count (430).
- Cocaine moved against its national decline in Regions 8 (+26.8%) and 9 (+16.3%); Region 8 fentanyl also increased (+15.2%).
- Numeric values were available for 95.8% of source records; source missingness/suppression was preserved.

## Validation performed

- Executed complete acquisition, cleaning, analysis, and visualization workflow.
- Passed seven programmatic QA checks and all automated output assertions.
- Verified row grain, monthly coverage, dimensions, ranges, data-as-of date, and output presence.
- Recorded raw-file and metadata SHA-256 checksums.
- Created U.S.–region reconciliation outputs.
- Cross-checked six Python headline values in the SAS program.
- Reviewed the dashboard at full resolution.
- Verified all five authoritative CDC/NCHS and HHS source links on October 20, 2026.
- Verified every internal Markdown file link resolves.
- Verified the staged website image is byte-for-byte identical to the final dashboard.
- Previewed the staged website card in a real browser and confirmed its image, copy, navigation, and accessibility text render correctly.

## Unresolved limitations

- SAS is not installed locally, so the SAS program was syntax-reviewed and designed for SAS Studio/SAS OnDemand but could not be executed in this environment.
- The source is provisional and may be revised.
- Counts are not rates, categories overlap, and small baselines can produce unstable percent changes.
- The compact log-linear model has seven annual observations and should not be used for forecasting.

## Proposed GitHub metadata

- **Repository:** `provisional-overdose-drug-signals`
- **Description:** `CDC/NCHS analysis of provisional drug-involved overdose mortality signals using SAS and Python, with national and HHS-region trend comparisons.`
- **Homepage:** `https://gorkira28.github.io/#work`
- **Topics:** `epidemiology`, `public-health`, `overdose-surveillance`, `mortality`, `cdc`, `nchs`, `sas`, `python`, `data-quality`, `data-visualization`

## GitHub portfolio audit

- The public profile currently has seven repositories, a concise role-aligned bio, the portfolio website, and **Available for hire** enabled.
- Existing public repositories use consistent, decision-focused descriptions and remain easy to scan.
- After publication, recommended pins are: `provisional-overdose-drug-signals`, `cms-ed-throughput-benchmarking`, `type-2-diabetes-trial-results-reporting`, `pertussis-2025-surveillance-priorities`, `nhanes-hypertension-awareness-gap`, and `texas-diabetes-vulnerability-atlas`. The website remains prominent through the profile Website field and does not need a pin.

## Exact publication bundle

### New project files

- `.gitignore`
- `CITATION.cff`
- `LICENSE`
- `README.md`
- `REVIEW_CHECKLIST.md`
- `RUN_SUMMARY.md`
- `requirements.txt`
- `run_pipeline.ps1`
- `python/acquire_and_analyze.py`
- `sas/overdose_signal_analysis.sas`
- `tests/test_outputs.py`
- `docs/data_dictionary.md`
- `docs/linkedin_post_draft.md`
- `docs/methodology.md`
- `docs/portfolio_case_study.md`
- `docs/references.md`
- `data/raw/cdc_dataset_metadata_2026-10-20.json`
- `data/raw/cdc_drug_involved_counts_2026-10-20.csv`
- `data/raw/manifest.json`
- `data/processed/annual_december_snapshots.csv`
- `data/processed/drug_involved_counts_clean.csv`
- `outputs/figures/overdose_drug_signal_dashboard.png`
- `outputs/tables/key_results.json`
- `outputs/tables/national_latest_yoy_change.csv`
- `outputs/tables/national_loglinear_trends.csv`
- `outputs/tables/qa_checks.csv`
- `outputs/tables/regional_latest_yoy_change.csv`
- `outputs/tables/us_region_reconciliation.csv`

### Staged portfolio files

- `../publish-profile/README.md`
- `../publish-site/index.html`
- `../publish-site/assets/overdose_drug_signal_dashboard.png`

## External actions awaiting approval

No remote repository, GitHub profile, portfolio website, or LinkedIn content was changed during this run.
