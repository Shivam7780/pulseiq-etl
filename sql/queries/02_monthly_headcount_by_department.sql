
-- Query 2: Monthly Headcount by Department

SELECT
    month_start_date,
    department_id,
    headcount_start,
    hires,
    exits,
    voluntary_exits,
    transfers_in,
    transfers_out,
    headcount_end,
    attrition_rate_monthly_pct
FROM warehouse_v2.fact_headcount_monthly
ORDER BY month_start_date, department_id;
