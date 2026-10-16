from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    COUNT(*) AS total_versions,
    COUNT(DISTINCT employee_id) AS unique_employees,
    COUNT(*) FILTER (WHERE is_current = TRUE) AS current_versions,
    COUNT(*) FILTER (WHERE valid_from IS NULL) AS missing_valid_from,
    COUNT(*) FILTER (WHERE valid_to IS NULL) AS open_ended_versions
FROM warehouse_v2.dim_employee
""")

with engine.connect() as connection:
    print(connection.execute(query).fetchone())

engine.dispose()
