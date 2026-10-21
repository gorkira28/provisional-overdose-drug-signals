/*
  CDC provisional drug-involved overdose mortality signals
  SAS Studio / SAS OnDemand-compatible validation and analysis workflow

  Before running, upload the project and change PROJECT_PATH below.
*/

%let project_path=/home/your-user/provisional-overdose-drug-signals;
%let raw_file=&project_path/data/raw/cdc_drug_involved_counts_2026-10-20.csv;
options validvarname=v7 mprint mlogic symbolgen;

/* 1. Deterministic CSV import and type conversion. */
data work.overdose_raw;
  infile "&raw_file" dsd firstobs=2 truncover lrecl=1048576;
  length data_as_of_char $23 death_year 8 death_month $12
         jurisdiction_occurrence $32 drug_involved $32 time_period $32
         month_ending_char $23 drug_overdose_deaths 8 footnote $500;
  informat drug_overdose_deaths best32.;
  input data_as_of_char :$23.
        death_year :best32.
        death_month :$12.
        jurisdiction_occurrence :$32.
        drug_involved :$32.
        time_period :$32.
        month_ending_char :$23.
        drug_overdose_deaths :best32.
        footnote :$500.;

  data_as_of = datepart(input(data_as_of_char, e8601dt.));
  month_ending_date = datepart(input(month_ending_char, e8601dt.));
  is_suppressed_or_missing = missing(drug_overdose_deaths);
  is_united_states = (jurisdiction_occurrence = "United States");
  is_hhs_region = (substr(jurisdiction_occurrence, 1, 7) = "Region ");
  is_december_snapshot = (month(month_ending_date) = 12);
  format data_as_of month_ending_date yymmdd10.;
  drop data_as_of_char month_ending_char;
run;

/* 2. QA/QC: row count, grain, dimensions, dates, and ranges. */
proc sql noprint;
  select count(*) into :n_rows trimmed from work.overdose_raw;
  select count(*) into :n_unique trimmed
  from (select distinct jurisdiction_occurrence, drug_involved, month_ending_date
        from work.overdose_raw);
  select count(distinct jurisdiction_occurrence), count(distinct drug_involved),
         count(distinct data_as_of), sum(not missing(drug_overdose_deaths)),
         max(month_ending_date)
    into :n_jurisdictions trimmed, :n_drugs trimmed, :n_asof trimmed,
         :n_available trimmed, :latest_date
  from work.overdose_raw;
  select count(*) into :n_negative trimmed
  from work.overdose_raw
  where drug_overdose_deaths < 0;
quit;

%macro assert_equal(label, actual, expected);
  %if %sysevalf(&actual = &expected) %then
    %put NOTE: PASS &label observed=&actual expected=&expected.;
  %else %do;
    %put ERROR: FAIL &label observed=&actual expected=&expected.;
    %abort cancel;
  %end;
%mend;

%assert_equal(Row count, &n_rows, 11088);
%assert_equal(Unique analytic grain, &n_unique, 11088);
%assert_equal(Jurisdictions, &n_jurisdictions, 11);
%assert_equal(Drug categories, &n_drugs, 12);
%assert_equal(Data-as-of values, &n_asof, 1);
%assert_equal(Available numeric counts, &n_available, 10625);
%assert_equal(Negative counts, &n_negative, 0);

/* 3. Annual December snapshots: adjacent observations cover non-overlapping years. */
data work.annual_december;
  set work.overdose_raw;
  where is_december_snapshot = 1;
run;

/* 4. Recreate national year-over-year table. */
proc sql;
  create table work.national_latest_yoy as
  select a.drug_involved,
         a.drug_overdose_deaths as latest_count,
         b.drug_overdose_deaths as previous_count,
         calculated latest_count - calculated previous_count as absolute_change,
         100 * calculated absolute_change / calculated previous_count as yoy_percent_change
  from work.overdose_raw as a
  left join work.overdose_raw as b
    on a.drug_involved = b.drug_involved
   and b.jurisdiction_occurrence = "United States"
   and b.month_ending_date = intnx('year', a.month_ending_date, -1, 'same')
  where a.jurisdiction_occurrence = "United States"
    and a.month_ending_date = &latest_date
  order by latest_count desc;
quit;

/* 5. Recreate regional change table. Missing/suppressed values remain missing. */
proc sql;
  create table work.regional_latest_yoy as
  select a.jurisdiction_occurrence, a.drug_involved,
         a.drug_overdose_deaths as latest_count,
         b.drug_overdose_deaths as previous_count,
         calculated latest_count - calculated previous_count as absolute_change,
         100 * calculated absolute_change / calculated previous_count as yoy_percent_change
  from work.overdose_raw as a
  left join work.overdose_raw as b
    on a.jurisdiction_occurrence = b.jurisdiction_occurrence
   and a.drug_involved = b.drug_involved
   and b.month_ending_date = intnx('year', a.month_ending_date, -1, 'same')
  where a.is_hhs_region = 1
    and a.month_ending_date = &latest_date
  order by a.drug_involved, a.jurisdiction_occurrence;
quit;

/* 6. Cross-check headline results calculated independently in Python. */
proc sql noprint;
  select latest_count, previous_count into :fentanyl_latest, :fentanyl_previous
  from work.national_latest_yoy where drug_involved = "Fentanyl";
  select latest_count, previous_count into :xylazine_latest, :xylazine_previous
  from work.national_latest_yoy where drug_involved = "Xylazine";
  select latest_count, previous_count into :ketamine_latest, :ketamine_previous
  from work.national_latest_yoy where drug_involved = "Ketamine";
quit;

%assert_equal(Fentanyl latest count, &fentanyl_latest, 36627);
%assert_equal(Fentanyl prior-year count, &fentanyl_previous, 47478);
%assert_equal(Xylazine latest count, &xylazine_latest, 2483);
%assert_equal(Xylazine prior-year count, &xylazine_previous, 6109);
%assert_equal(Ketamine latest count, &ketamine_latest, 430);
%assert_equal(Ketamine prior-year count, &ketamine_previous, 368);

/* 7. Exploratory log-linear trend model using non-overlapping annual counts. */
data work.annual_us;
  set work.annual_december;
  where is_united_states = 1 and drug_overdose_deaths > 0;
  log_count = log(drug_overdose_deaths);
  year_index = death_year - 2019;
run;

proc sort data=work.annual_us;
  by drug_involved;
run;

ods exclude all;
ods output ParameterEstimates=work.trend_parameters;
proc reg data=work.annual_us;
  by drug_involved;
  model log_count = year_index / clb;
quit;
ods exclude none;

data work.sas_loglinear_trends;
  set work.trend_parameters;
  where variable = "year_index";
  model_apc_percent = 100 * (exp(estimate) - 1);
  model_apc_ci_low = 100 * (exp(lowercl) - 1);
  model_apc_ci_high = 100 * (exp(uppercl) - 1);
  keep drug_involved estimate stderr probt lowercl uppercl
       model_apc_percent model_apc_ci_low model_apc_ci_high;
run;

/* 8. Export SAS results for direct comparison with Python outputs. */
proc export data=work.national_latest_yoy
  outfile="&project_path/outputs/tables/sas_national_latest_yoy_change.csv"
  dbms=csv replace;
run;

proc export data=work.regional_latest_yoy
  outfile="&project_path/outputs/tables/sas_regional_latest_yoy_change.csv"
  dbms=csv replace;
run;

proc export data=work.sas_loglinear_trends
  outfile="&project_path/outputs/tables/sas_loglinear_trends.csv"
  dbms=csv replace;
run;

title "National provisional drug-involved overdose mortality signals";
proc print data=work.national_latest_yoy noobs label;
  format latest_count previous_count absolute_change comma12.
         yoy_percent_change 8.1;
run;
title;
