# Data dictionary

## Source fields

| Field | Meaning |
|---|---|
| `data_as_of` | NCHS release cutoff date recorded in the source |
| `death_year` | Calendar year of the 12-month ending period |
| `death_month` | Month name of the period endpoint |
| `jurisdiction_occurrence` | United States or one of 10 HHS regions |
| `drug_involved` | Drug named on the death certificate; categories can overlap |
| `time_period` | Source period label |
| `month_ending_date` | Final date of the rolling 12-month period |
| `drug_overdose_deaths` | Provisional drug-involved overdose death count; missing when suppressed/unavailable |
| `footnote` | Source notes, including suppression information |

## Derived fields

| Field | Meaning |
|---|---|
| `is_suppressed_or_missing` | Count could not be analyzed numerically |
| `is_united_states` | Row is the national aggregate |
| `is_hhs_region` | Row is one of the 10 HHS-region aggregates |
| `is_december_snapshot` | Period ends in December and is included in annual trend summaries |
| `absolute_change` | Latest count minus prior-year count |
| `yoy_percent_change` | Percent change from the same period endpoint one year earlier |
| `model_apc_percent` | Exploratory annual percent change from the log-linear model |
