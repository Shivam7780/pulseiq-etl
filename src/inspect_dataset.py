
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "clean" / "pulseiq_cleaned.xlsx"

df = pd.read_excel(FILE, sheet_name="fact_task")

print("\n--- FACT_TASK COLUMNS ---")
for column in df.columns:
    print(column)

print("\n--- SAMPLE TASK RECORDS ---")
print(df.head(10).to_string(index=False))

print("\n--- TASK DATA TYPES ---")
print(df.dtypes)
