import pandas as pd

path = r"data/raw/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

metrics = pd.read_excel(path, sheet_name="metric_dictionary")
mask = metrics.astype(str).apply(
    lambda col: col.str.contains("transfer", case=False, na=False)
).any(axis=1)

print("TRANSFER-RELATED METRICS")
print("=" * 60)
if mask.any():
    print(metrics.loc[mask].to_string(index=False))
else:
    print("No transfer-specific metric found.")

print("\nEMPLOYEE DATA CONTRACTS")
contracts = pd.read_excel(path, sheet_name="data_contracts")
print(contracts[
    contracts.astype(str).apply(
        lambda col: col.str.contains("employee|valid_from|valid_to|is_current",
                                     case=False, na=False)
    ).any(axis=1)
].to_string(index=False))
