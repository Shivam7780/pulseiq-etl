import pandas as pd
from sqlalchemy import create_engine, text

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
df = pd.read_excel(path, sheet_name="dim_employee")

df["is_current"] = (
    df["is_current"].astype(str).str.strip().str.upper()
)

print("SOURCE EXCEL")
print("Total versions:", len(df))
print("Unique employees:", df["employee_id"].nunique())
print("Current versions:", (df["is_current"] == "Y").sum())
print("Historical versions:", (df["is_current"] == "N").sum())

engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

query = text("""
SELECT
    COUNT(*) AS total_versions,
    COUNT(DISTINCT employee_id) AS unique_employees,
    COUNT(*) FILTER (WHERE is_current = TRUE) AS current_versions
FROM warehouse_v2.dim_employee
""")

with engine.connect() as connection:
    print("\nEXISTING WAREHOUSE")
    print(connection.execute(query).fetchone())

engine.dispose()
