import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

df = pd.read_excel(
    path,
    sheet_name="reference_summary_dept_month"
)

print("Columns:")
print(df.columns.tolist())

print("\nRow count:", len(df))
print("\nFirst 5 rows:")
print(df.head().to_string(index=False))

