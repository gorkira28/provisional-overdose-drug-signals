# LinkedIn post draft

National declines can hide local signals moving in the opposite direction.

That was the clearest lesson from my latest public-health analytics project.

I analyzed 11,088 CDC/NCHS records covering 12 drug-involvement categories across the United States and 10 HHS regions. I used non-overlapping annual snapshots so the December 2025 period could be compared fairly with December 2024.

Three findings stood out:

• Fentanyl remained the largest tracked category at 36,627 deaths, but its provisional count was 22.9% lower than the prior annual period.
• Xylazine showed the steepest national decline at 59.4%.
• Ketamine increased 16.8% nationally, while cocaine increased 26.8% in HHS Region 8 and 16.3% in Region 9 despite a 13.1% national decline.

I built the workflow in Python and added an independent SAS validation program for import, cleaning, QA checks, summary tables and log-linear trend modeling.

The most important limitation: these are provisional counts, not population-adjusted rates. Drug categories can overlap, and a death involving multiple drugs may appear in more than one category. The results describe surveillance signals—not risk, causation or program impact.

What additional information would you want before turning a national drug-overdose trend into a regional response decision?

P.S. I’ll share the complete code, methods and dashboard in the first comment.

#Epidemiology #SAS #HealthcareAnalytics

## First comment

Complete project, code, methods and outputs: https://github.com/gorkira28/provisional-overdose-drug-signals
