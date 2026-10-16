# PulseIQ Metric Dictionary

## Purpose
Definitions of key workforce analytics metrics used in the PulseIQ Analytics Warehouse.

| Metric ID | Metric Name | Definition | Calculation / Interpretation |
|---|---|---|---|
| M01 | Monthly Headcount | Number of employees active in a given month. | Count active employees for the selected month, using the warehouse headcount definition. |
| M02 | Monthly Payroll Cost | Total payroll cost for a selected month. | Sum the applicable employer payroll cost for the month. |
| M03 | Attendance Rate | Share of scheduled workdays counted as attended. | (SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / SUM(scheduled_days) * 100. Higher is better. |
| M04 | Leave Days by Type | Leave days grouped by leave type. | Sum recorded leave days for each leave type over the selected period. |
| M05 | Late Arrival Rate | Share of present days associated with late arrivals. | SUM(late_arrivals) / SUM(present_days) * 100. Lower is better. |

## Attendance Analysis Notes
- Attendance rate target: 94%.
- Attendance trends should be reviewed by month and department.
- AI-flagged months should be labelled "AI flag" in charts.
- The available attendance facts are monthly aggregates; weekday-level attendance rates must not be inferred unless daily or weekday-level source data is available.
- Metric results depend on the completeness and definitions of the source data. Validate the relevant warehouse columns before interpreting results.

## Limitations
These definitions document the intended metric logic. Confirm each calculation against the implemented SQL and source columns before treating it as a formally validated business definition.
