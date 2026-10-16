import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

xls = pd.ExcelFile(path)
print("Available sheets:")
print(xls.sheet_names)

for sheet in xls.sheet_names:
    if "employee" in sheet.lower():
        df = pd.read_excel(path, sheet_name=sheet)
        print(f"\nSheet: {sheet}")
        print("Columns:", df.columns.tolist())
        print(df.head(5).to_string(index=False))

