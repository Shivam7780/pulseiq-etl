from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('dw', 'warehouse_v2')
  AND table_type = 'BASE TABLE'
ORDER BY table_schema, table_name
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)

engine.dispose()
