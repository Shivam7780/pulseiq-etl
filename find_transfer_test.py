import pandas as pd

path = r"data/clean/pulseiq_cleaned.xlsx"
df = pd.read_excel(path, sheet_name="dim_employee")
df["valid_from"] = pd.to_datetime(df["valid_from"], errors="coerce")
df["valid_to"] = pd.to_datetime(df["valid_to"], errors="coerce")

df = df.sort_values(["employee_id", "valid_from", "employee_key"])

for employee_id, group in df.groupby("employee_id"):
    group = group.reset_index(drop=True)

    for i in range(1, len(group)):
        previous = group.iloc[i - 1]
        current = group.iloc[i]

        if (
            previous["department_id"] != current["department_id"]
            and str(current["change_reason"]).strip().lower() == "transfer"
        ):
            print("TRANSFER TEST CANDIDATE")
            print("Employee:", employee_id)
            print(
                group.loc[
                    group.index.isin([i - 1, i]),
                    [
                        "employee_key", "employee_id", "department_id",
                        "role_id", "valid_from", "valid_to",
                        "is_current", "change_reason"
                    ]
                ].to_string(index=False)
            )
            raise SystemExit

print("No consecutive department change marked Transfer was found.")
