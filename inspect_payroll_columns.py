from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'warehouse_v2'
  AND table_name = 'fact_payroll'
ORDER BY ordinal_position
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)

engine.dispose()
