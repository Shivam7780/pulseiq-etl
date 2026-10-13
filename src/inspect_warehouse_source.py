
import pandas as pd

file_path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

excel = pd.ExcelFile(file_path)

print("SOURCE WORKBOOK SHEETS")
print("=" * 60)

for sheet in excel.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet, nrows=3)

    print(f"\n--- {sheet} ---")
    print("Columns:", list(df.columns))
    print("Sample rows:", len(df))
