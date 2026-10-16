from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.constraint_schema = kcu.constraint_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
   AND ccu.constraint_schema = tc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_schema = 'warehouse_v2'
  AND ccu.table_name = 'dim_employee'
  AND ccu.column_name = 'employee_key'
ORDER BY tc.table_name
""")

with engine.connect() as connection:
    rows = connection.execute(query).fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No foreign keys reference warehouse_v2.dim_employee.employee_key.")

engine.dispose()
