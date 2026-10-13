import pandas as pd
from pathlib import Path

FILE_PATH = Path("data/clean/pulseiq_cleaned.xlsx")
SHEET_NAME = "fact_payroll"


def validate_payroll():
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)

    required = {"employee_id", "net_pay", "gross_pay"}

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing payroll columns: {sorted(missing)}")

    for column in ["net_pay", "gross_pay"]:
        df[column] = pd.to_numeric(df[column], errors="raise")

        if (df[column].dropna() < 0).any():
            raise ValueError(f"Validation failed: negative values in {column}")

    if df["employee_id"].isna().any():
        raise ValueError("Validation failed: missing employee IDs in payroll")

    print("PAYROLL VALIDATION PASSED")
    print(f"Payroll rows validated: {len(df)}")
    print(f"Missing employee IDs: {df['employee_id'].isna().sum()}")


if __name__ == "__main__":
    validate_payroll()