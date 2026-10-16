import pandas as pd
from pathlib import Path

path = Path("data/clean/pulseiq_cleaned.xlsx")
xls = pd.ExcelFile(path)

print("Workbook:", path)
print("\nAvailable sheets:")
for sheet in xls.sheet_names:
    print("-", sheet)

matches = [s for s in xls.sheet_names if "employee_assignments" in s.lower()]

for sheet in matches:
    df = pd.read_excel(path, sheet_name=sheet)
    print(f"\n--- {sheet} ---")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print(df.head(10).to_string(index=False))
