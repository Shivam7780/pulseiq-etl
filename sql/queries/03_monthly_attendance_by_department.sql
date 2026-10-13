
SELECT
    DATE_TRUNC('month', period_end_date)::date AS attendance_month,
    department_id,
    COUNT(*) AS attendance_records,
    COUNT(DISTINCT employee_key) AS employees_tracked,
    SUM(present_days) AS total_present_days,
    SUM(scheduled_days) AS total_scheduled_days,
    ROUND(
        100.0 * SUM(present_days)
        / NULLIF(SUM(scheduled_days), 0),
        2
    ) AS attendance_rate_pct
FROM warehouse_v2.fact_attendance
WHERE period_end_date IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
