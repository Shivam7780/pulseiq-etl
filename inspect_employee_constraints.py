from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    tc.constraint_type,
    tc.constraint_name,
    kcu.column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.table_schema = kcu.table_schema
   AND tc.table_name = kcu.table_name
WHERE tc.table_schema = 'warehouse_v2'
  AND tc.table_name = 'dim_employee'
ORDER BY tc.constraint_type, tc.constraint_name, kcu.ordinal_position
""")

with engine.connect() as connection:
    for row in connection.execute(query):
        print(row)

engine.dispose()
