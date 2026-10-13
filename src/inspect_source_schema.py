
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

with open("reports/source_schema.txt", "w", encoding="utf-8") as f:
    for table in tables:
        df = pd.read_excel(file_path, sheet_name=table, nrows=0)
        f.write(f"\n--- {table} ---\n")
        f.write(", ".join(df.columns.tolist()) + "\n")

print("Source schema saved to reports/source_schema.txt")
