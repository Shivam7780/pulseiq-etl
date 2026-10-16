from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    COUNT(*) FILTER (
        WHERE is_current = TRUE
          AND valid_to = DATE '9999-12-31'
    ) AS current_with_open_end_date,

    COUNT(*) FILTER (
        WHERE is_current = TRUE
          AND valid_to <> DATE '9999-12-31'
    ) AS current_with_other_end_date,

    COUNT(*) FILTER (
        WHERE is_current = FALSE
          AND valid_to = DATE '9999-12-31'
    ) AS historical_with_open_end_date,

    COUNT(*) FILTER (
        WHERE valid_to < valid_from
    ) AS reversed_date_ranges
FROM warehouse_v2.dim_employee
""")

with engine.connect() as connection:
    print(connection.execute(query).fetchone())

engine.dispose()
