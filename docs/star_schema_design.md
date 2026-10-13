# PulseIQ Analytics Warehouse ? Star Schema Design

## 1. Business Questions

1. What is the monthly payroll cost by department and role?
2. How does employee headcount change each month?
3. What are attendance rates by department and month?
4. How many employees join or leave each month?
5. How many leave days are used by leave type?
6. Which departments have the highest overtime costs?
7. How do payroll costs change when an employee transfers between departments?

## 2. Dimension Tables

- **dim_employee** ? Employee identity and history, including `valid_from`, `valid_to`, and `is_current`.
- **dim_department** ? Department details.
- **dim_role** ? Role or job-title details.
- **dim_date** ? Calendar date, month, quarter, and year attributes.
- **dim_leave_type** ? Leave type and policy details.

## 3. Fact Tables and Grain

- **fact_attendance** ? One row per employee per attendance reporting period, identified by `attendance_fact_id` and associated with `period_end_date`.
- **fact_payroll** ? One row per payroll item, identified by `payroll_item_id`.
- **fact_leave** ? One row per leave request, identified by `leave_request_id`.
- **fact_headcount_monthly** ? One row per department per monthly snapshot, uniquely identified by (`date_key`, `department_id`).

## 4. Historical Dimension Strategy

The employee dimension uses Slowly Changing Dimension Type 2 history. The fields `valid_from`, `valid_to`, and `is_current` identify effective-dated employee versions. Historical facts should retain the employee version applicable to their event date so that transfers do not rewrite earlier departmental costs.

Department Type 2 history should only be claimed if effective-dated department versions are implemented in the dimension.

## 5. Loading Strategy

- Load dimensions before dependent fact tables.
- Use stable business keys.
- Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` for repeatable loads where appropriate.
- Index fact-table foreign keys and commonly filtered date keys.
- Validate warehouse totals against cleaned source files.
- Quarantine rejected records and retain data-quality reports.

## 6. Data Quality and Reconciliation

- Validate business keys and required fields.
- Check employee history date ranges for validity and overlap.
- Flag invalid attendance, payroll, and leave records.
- Confirm fact-table grain and prevent duplicate business-key combinations.
- Compare SQL query results with cleaned source data and document exclusions.
