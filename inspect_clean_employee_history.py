import pandas as pd

path = r"data/clean/pulseiq_cleaned.xlsx"
df = pd.read_excel(path, sheet_name="dim_employee")

print("Rows:", len(df))
print("Columns:")
for col in df.columns:
    print("-", col)

print("\nFirst 10 rows:")
print(df.head(10).to_string(index=False))

print("\nTransfer-related rows, if a change-reason column exists:")
reason_col = next(
    (c for c in df.columns if c.lower() in ["change_reason", "reason"]),
    None
)
if reason_col:
    mask = df[reason_col].astype(str).str.contains("transfer", case=False, na=False)
    print(df.loc[mask].head(10).to_string(index=False))
    print("Transfer-related rows:", int(mask.sum()))
else:
    print("No change_reason or reason column found.")
