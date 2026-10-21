# Methodology

## Decision question

Which drug-involvement signals changed most in the latest comparable 12-month periods, and where did HHS regional patterns differ from the national direction?

## Source and analytic unit

The source is the CDC/NCHS dataset **Provisional drug overdose death counts for specific drugs** (`8hzs-zshh`), retrieved from Data.CDC.gov on October 20, 2026. Each row represents one drug category, one geography, and one 12-month ending period. The release reports the data as of July 5, 2026 and extends through the 12-month period ending December 31, 2025.

The 12 drug categories are not mutually exclusive. A death involving more than one listed drug can appear in multiple categories. Counts between 1 and 9 may be suppressed under NCHS confidentiality standards.

## Comparison design

The primary comparison uses December 2025 versus December 2024. Each value covers the preceding 12 months, so these adjacent December snapshots represent non-overlapping annual periods. Month-to-month comparisons were deliberately avoided because consecutive 12-month rolling windows share 11 months of data.

National and regional change are reported as:

`100 × (December 2025 count − December 2024 count) / December 2024 count`

Counts are not population-adjusted rates and are not used to rank population risk across HHS regions.

## Exploratory trend model

For each drug category, a log-linear model is fit to positive U.S. December counts from 2019–2025:

`log(count) = intercept + beta × year`

The modeled annual percent change is `100 × (exp(beta) − 1)`. Confidence intervals use the ordinary least-squares standard error of the slope. With only seven annual observations, this is a compact descriptive trend summary, not a forecasting or causal model. Early counts for emerging substances can make the constant-slope assumption especially weak.

Python generates the published outputs. SAS independently imports and cleans the source snapshot, recreates national and regional change tables, checks headline counts, and fits the same log-linear model.

## Quality controls

- Preserved the complete 11,088-row source extract and dataset metadata.
- Recorded SHA-256 checksums and retrieval time in `data/raw/manifest.json`.
- Verified the expected geography × drug × month grain with zero duplicates.
- Verified 11 jurisdictions, 12 drug categories, one data-as-of date, a complete monthly sequence, and nonnegative numeric counts.
- Retained suppressed or unavailable values as missing; no imputation was performed.
- Reconciled the published U.S. value with the sum of HHS-region values as a diagnostic, while recognizing that suppression can create small differences.
- Embedded SAS assertions for row counts and six independently reproduced headline values.

## Interpretation boundaries

The analysis is surveillance-oriented. It cannot establish why a count changed, whether the change is statistically or operationally meaningful, or whether a policy or intervention caused it. Provisional data can be revised, and reporting completeness may vary. Drug categories overlap. HHS regions differ in population size and composition, so regional counts and percentage changes do not measure relative risk.
