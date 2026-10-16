from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    column_default,
    is_identity,
    identity_generation
FROM information_schema.columns
WHERE table_schema = 'warehouse_v2'
  AND table_name = 'dim_employee'
  AND column_name = 'employee_key'
""")

with engine.connect() as connection:
    print(connection.execute(query).fetchone())

engine.dispose()
