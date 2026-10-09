# Motor Insurance Claims & Policy Analytics

## 1. Executive Summary

This project analyzes motor insurance customers, vehicles, policies, claims, and payments through a Python data-processing pipeline, statistical analysis, visualizations, and an interactive Streamlit dashboard.

The available dataset contains 20,000 customers, 25,000 vehicles, 25,000 policies, 10,000 claims, and 7,000 payment records. The analysis focuses on policy portfolio composition, premium amounts, claim status, claim severity, settlement duration, customer and vehicle characteristics, and payment activity.

The objective is to convert related insurance datasets into understandable business information that supports monitoring, investigation, and further analysis. The findings are descriptive and should not be treated as proof of causation or actuarial conclusions.

## 2. Business Objectives

* Assess the composition of the policy portfolio.
* Summarize premium and coverage amounts.
* Analyze claim volume, status, type, and amount.
* Examine settlement duration and payment records.
* Explore customer, vehicle, and geographic patterns.
* Identify data-quality concerns.
* Present findings through charts, KPIs, and an interactive dashboard.

## 3. Data Sources and Relationships

The project uses five related tables:

| Dataset   | Recorded rows | Purpose                                     |
| --------- | ------------: | ------------------------------------------- |
| Customers |        20,000 | Customer demographics and location          |
| Vehicles  |        25,000 | Vehicle characteristics and recorded value  |
| Policies  |        25,000 | Policy status, premium, coverage, and dates |
| Claims    |        10,000 | Claim amounts, types, statuses, and dates   |
| Payments  |         7,000 | Payment amounts, dates, status, and method  |

The data model connects vehicles and policies to customers, claims to policies and customers, and payments to claims and policies through their identifier columns.

## 4. Data Preparation and Quality

The pipeline loads the raw tables, checks primary keys and foreign-key relationships, cleans data, derives analytical columns, and saves cleaned CSV files.

The preparation workflow preserves missing values when they cannot be reliably inferred and avoids inventing missing approval or settlement dates.

Two important data-quality observations were recorded:

* Some claims have missing approval or settlement dates. These may be legitimate for claims that have not reached those workflow stages.
* Fifty-nine policies have end dates earlier than their start dates. These records are preserved and flagged for investigation rather than silently removed.

Data-quality warnings should be reviewed by the appropriate business owner before the records are used for operational decisions.

## 5. Policy Portfolio Findings

The recorded portfolio contains 25,000 policies, of which 7,551 have the status Active in the dataset.

Total recorded premium is approximately ₹79.56 crore. The average premium is approximately ₹31,823 per policy.

These values summarize the available policy records. They do not, by themselves, establish profitability, policy renewal performance, or the adequacy of pricing. Such conclusions would require additional context, including exposure periods, costs, and business targets.

## 6. Claims Findings

The dataset contains 10,000 claim records with a total recorded claim amount of approximately ₹288.54 crore. The average recorded claim amount is approximately ₹2.89 lakh.

The recorded claim statuses are:

| Claim status | Records |
| ------------ | ------: |
| Approved     |   3,790 |
| Settled      |   3,259 |
| Pending      |   1,791 |
| Rejected     |   1,160 |
| Total        |  10,000 |

The approval-status share is 37.9% when calculated as Approved records divided by all claim records. The settlement-status share is 32.59% when calculated as Settled records divided by all claim records.

These are status proportions, not necessarily final approval or settlement rates for a fully matured cohort of claims. Approved and Settled are treated as separate status categories in this dataset.

## 7. Premium, Claims, and Payments

The recorded total claim amount divided by total recorded premium is approximately 362.69%.

This is a descriptive ratio of the totals in the available dataset. It is not automatically a formal insurance loss ratio: the available records do not establish that claim amounts and premium amounts represent matching earned-exposure periods.

Total recorded payment amount is approximately ₹176.69 crore across 7,000 payment records.

Claim amount and payment amount represent different business measures. A claim may have a recorded claim amount that differs from the amount paid. Payment status and claim status must therefore be analyzed separately.

## 8. Settlement Performance

The previously generated analysis reported an average claim settlement duration of approximately 23.93 days for records with usable settlement-duration values.

This value should be interpreted alongside the number of records used to calculate it, the treatment of missing dates, and the definition of the duration. Claims without a settlement date should not be assigned an invented settlement duration.

Further analysis should compare settlement duration by claim type, damage severity, region, and claim status where sample sizes are sufficient.

## 9. Customer and Vehicle Analysis

The dashboard includes customer demographics, geography, occupation, vehicle type, fuel type, vehicle age, and their relationships with recorded claims.

The current vehicle dataset contains only the Car category for vehicle type. Consequently, comparisons between different vehicle types are not supported by the current source data. The dashboard should report this limitation rather than invent additional categories.

Differences in claim counts or claim amounts across customer or vehicle groups are descriptive associations. They do not establish that a characteristic caused a claim or increased risk.

## 10. Dashboard and Deliverables

The interactive Streamlit dashboard provides:

* Executive KPIs for customers, vehicles, policies, premiums, claims, and payments.
* Policy status and policy-type analysis.
* Premium and claim amount distributions and trends.
* Claim status, type, severity, and geographic views.
* Customer and vehicle analysis.
* Payment and settlement analysis.
* Evidence-based business observations and recommendations.
* Filtered table previews and CSV downloads.

The supporting project includes the raw and cleaned datasets, Python source modules, an analysis notebook, chart outputs, automated tests, pipeline logs, and this business report.

## 11. Recommendations

1. Investigate the 59 policies with reversed start and end dates.
2. Review missing claim workflow dates in the context of the corresponding claim statuses.
3. Monitor pending claims and settlement durations using clearly defined operational targets.
4. Compare recorded claim amounts with payment amounts and payment statuses.
5. Assess policy performance using suitable exposure periods and earned-premium measures before drawing actuarial conclusions.
6. Collect additional vehicle categories if cross-category vehicle analysis is a business requirement.
7. Validate dashboard KPIs against independent calculations before using them in operational reporting.

## 12. Limitations

* The findings reflect the supplied datasets and their recorded values.
* Missing values and anomalous dates may affect individual analyses.
* The vehicle-type field contains only Car records, limiting category comparisons.
* Recorded claim-to-premium ratios are not formal loss ratios without appropriate exposure and earned-premium definitions.
* Observational patterns do not prove causation.
* Business recommendations should be reviewed against company policy, operational context, and appropriate subject-matter expertise.

## 13. Conclusion

The project establishes a repeatable workflow for preparing and analyzing related motor insurance datasets. Its KPIs, visualizations, tests, and interactive dashboard provide a foundation for exploring policy portfolios, claims, settlements, and payments.

Before final submission, the project should pass its full automated test suite, the dashboard should be verified under both default and filtered views, and the reported values should be checked against independently calculated results.
