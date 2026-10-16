from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'dw'
ORDER BY table_name
""")

with engine.connect() as connection:
    rows = connection.execute(query).fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("Schema dw has no visible tables, or does not exist.")
        
    schema_query = text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'dw'
    """)
    print("Schema exists:", connection.execute(schema_query).first() is not None)

engine.dispose()
