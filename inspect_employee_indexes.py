from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'warehouse_v2'
  AND tablename = 'dim_employee'
ORDER BY indexname
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)

engine.dispose()
