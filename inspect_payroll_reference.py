import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

for sheet in ["fact_payroll", "reconciliation_answer_key"]:
    df = pd.read_excel(path, sheet_name=sheet)
    print(f"\n--- {sheet} ---")
    print("Columns:", df.columns.tolist())
    print("Rows:", len(df))
    print(df.head(5).to_string(index=False))

