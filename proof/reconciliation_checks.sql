-- Task 2: Warehouse reconciliation proof

-- Check 1: Employer cost for payroll run PR-2025-04
SELECT ROUND(SUM(employer_cost), 2) AS employer_cost
FROM dw.fact_payroll
WHERE run_id = 'PR-2025-04';
-- Expected: 53363392.08

-- Check 2: Employees paid in payroll run PR-2026-09
SELECT COUNT(DISTINCT employee_key) AS employees_paid
FROM dw.fact_payroll
WHERE run_id = 'PR-2026-09';
-- Expected: 444

-- Check 3: Department D00, April 2025
SELECT
    department_id,
    month,
    employer_cost,
    gross_pay,
    employees_paid
FROM reference_summary_dept_month
WHERE department_id = 'D00'
  AND month = '2025-04';
-- Expected: employer_cost 480809.00, gross_pay 479009.00, employees_paid 1
