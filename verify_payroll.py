from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    run_id,
    COUNT(DISTINCT employee_key)
        FILTER (WHERE headcount_flag = 1) AS paid_employees,
    ROUND(SUM(gross_pay)::numeric, 2) AS gross_pay,
    ROUND(SUM(net_pay)::numeric, 2) AS net_pay,
    ROUND(SUM(employer_cost)::numeric, 2) AS employer_cost
FROM warehouse_v2.fact_payroll
WHERE run_id IN ('PR-2025-04', 'PR-2026-09')
GROUP BY run_id
ORDER BY run_id
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)
