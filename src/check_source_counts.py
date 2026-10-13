
import pandas as pd

file_path = "data/clean/pulseiq_cleaned.xlsx"

tables = [
    "dim_employee",
    "dim_department",
    "dim_role",
    "dim_date",
    "dim_leave_type",
    "fact_payroll",
    "fact_attendance_monthly",
    "fact_leave",
    "fact_headcount_monthly",
]

print("SOURCE TABLE ROW COUNTS")
print("-" * 45)

for table in tables:
    df = pd.read_excel(file_path, sheet_name=table)
    print(f"{table}: {len(df):,} rows")
