# Motor Insurance Data Quality Report

## Dataset summary

| dataset   | check                    |   issue_count | details                |
|:----------|:-------------------------|--------------:|:-----------------------|
| customers | row_count                |         20000 | 20000 rows, 8 columns  |
| customers | missing_required_columns |             0 | None                   |
| vehicles  | row_count                |         25000 | 25000 rows, 8 columns  |
| vehicles  | missing_required_columns |             0 | None                   |
| policies  | row_count                |         25000 | 25000 rows, 10 columns |
| policies  | missing_required_columns |             0 | None                   |
| claims    | row_count                |         10000 | 10000 rows, 12 columns |
| claims    | missing_required_columns |             0 | None                   |
| payments  | row_count                |          7000 | 7000 rows, 7 columns   |
| payments  | missing_required_columns |             0 | None                   |

## Findings requiring review

| dataset   | check            | column          |   issue_count | details                                    |
|:----------|:-----------------|:----------------|--------------:|:-------------------------------------------|
| claims    | missing_values   | approval_date   |          2951 | Detected dtype: str                        |
| claims    | missing_values   | settlement_date |          6741 | Detected dtype: str                        |
| policies  | end_before_start | policy_end_date |            59 | Policy end date precedes policy start date |
