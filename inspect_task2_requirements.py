import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
xls = pd.ExcelFile(path)

print("Available requirement-related sheets:")
for sheet in xls.sheet_names:
    if any(word in sheet.lower() for word in [
        "contract", "dq_checks", "dictionary", "reference_summary", "answer_key"
    ]):
        print("\n---", sheet, "---")
        df = pd.read_excel(path, sheet_name=sheet)
        print("Columns:", list(df.columns))
        print(df.head(8).to_string(index=False))
