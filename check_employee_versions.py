from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT employee_id, valid_from, COUNT(*) AS version_count
FROM warehouse_v2.dim_employee
GROUP BY employee_id, valid_from
HAVING COUNT(*) > 1
ORDER BY employee_id, valid_from
""")

with engine.connect() as connection:
    rows = connection.execute(query).fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("No duplicate employee versions found.")

engine.dispose()
