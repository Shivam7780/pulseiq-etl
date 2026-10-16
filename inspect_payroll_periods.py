from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    run_id,
    MIN(period_end_date) AS first_period_end,
    MAX(period_end_date) AS last_period_end,
    COUNT(*) AS payroll_rows
FROM warehouse_v2.fact_payroll
GROUP BY run_id
ORDER BY run_id
LIMIT 10
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)

engine.dispose()
