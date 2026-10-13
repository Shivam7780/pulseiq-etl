
-- Query 1: Monthly Payroll Cost by Department
-- Business question: What is the monthly payroll cost by department?

SELECT
    DATE_TRUNC('month', period_end_date)::date AS payroll_month,
    department_id,
    COUNT(*) AS payroll_records,
    COUNT(DISTINCT employee_key) AS employees_paid,
    SUM(gross_pay) AS total_gross_pay,
    SUM(net_pay) AS total_net_pay,
    SUM(employer_cost) AS total_employer_cost
FROM warehouse_v2.fact_payroll
WHERE period_end_date IS NOT NULL
GROUP BY
    DATE_TRUNC('month', period_end_date)::date,
    department_id
ORDER BY
    payroll_month,
    department_id;
