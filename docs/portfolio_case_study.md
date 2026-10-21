# Portfolio case study: Provisional overdose drug signals

## The question

Which drug-involvement signals changed most in the latest comparable annual periods, and where did HHS regional patterns diverge from the national direction?

## What I built

I created a reproducible CDC/NCHS surveillance workflow using Python and SAS. Python acquires the 11,088-row public dataset, preserves a checksum manifest, validates the analytic grain, creates non-overlapping annual snapshots, calculates national and HHS-region changes, fits exploratory log-linear trend models, and produces a recruiter-ready dashboard. A separate SAS program independently imports and cleans the data, recreates the primary tables, checks six headline counts, and fits the companion trend model.

## What the analysis found

In the 12-month period ending December 2025, fentanyl remained the largest of the 12 tracked drug-involvement categories at 36,627 deaths, while its count was 22.9% lower than the comparable December 2024 period. Xylazine had the steepest national decline (−59.4%). Ketamine was the fastest-growing national category (+16.8%), although its count was much smaller (430). Regional movement was not uniform: cocaine counts increased 26.8% in HHS Region 8 and 16.3% in Region 9 even as the national cocaine count declined 13.1%.

## Why it matters

A falling national count can hide substances or regions moving in the opposite direction. This workflow demonstrates how a surveillance analyst can separate broad progress from emerging exceptions without treating provisional counts as final estimates, population risk, or evidence of causation.

**Tools:** SAS, Python, CDC/NCHS data, reproducible acquisition, QA/QC, trend modeling, data visualization
