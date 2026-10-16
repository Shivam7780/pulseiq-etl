from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT employee_id, valid_from, valid_to, is_current
FROM warehouse_v2.dim_employee
WHERE valid_to < valid_from
   OR (is_current = TRUE AND valid_to IS NOT NULL)
ORDER BY employee_id, valid_from
""")

with engine.connect() as connection:
    rows = connection.execute(query).fetchall()
    if rows:
        print("Invalid employee date ranges or current-version markers:")
        for row in rows:
            print(row)
    else:
        print("No invalid date ranges or current-version markers found.")

engine.dispose()
