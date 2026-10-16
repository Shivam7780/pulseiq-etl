import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
df = pd.read_excel(path, sheet_name="dim_employee")

print("Total rows:", len(df))
print("Unique employee keys:", df["employee_key"].nunique())
print("Missing employee keys:", df["employee_key"].isna().sum())
print("Duplicate employee keys:", df["employee_key"].duplicated().sum())

print("\nExample employee history:")
cols = [
    "employee_key", "employee_id", "valid_from",
    "valid_to", "is_current", "change_reason"
]
print(
    df.loc[df["employee_id"] == "EMP-0001", cols]
      .to_string(index=False)
)
