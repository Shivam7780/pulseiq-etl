
from pathlib import Path

import pandas as pd
import pandera.pandas as pa


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"


def validate_employees():
    employees = pd.read_excel(DATA_FILE, sheet_name="dim_employee")

    employees["employee_id"] = (
        employees["employee_id"].astype("string").str.strip().str.upper()
    )
    employees["is_current"] = (
        employees["is_current"].astype("string").str.strip().str.upper()
    )

    schema = pa.DataFrameSchema(
        {
            "employee_id": pa.Column(str, nullable=False),
            "hire_date": pa.Column(pa.DateTime, nullable=True, coerce=True),
            "is_current": pa.Column(
                str,
                checks=pa.Check.isin(["Y", "N"]),
                nullable=False,
            ),
        },
        strict=False,
        coerce=True,
    )

    current = employees[employees["is_current"] == "Y"].copy()

    if current["employee_id"].duplicated().any():
        raise ValueError("Validation failed: duplicate current employee IDs found.")

    schema.validate(employees)

    print("EMPLOYEE VALIDATION PASSED")
    print(f"Total employee records: {len(employees)}")
    print(f"Current employee records: {len(current)}")
    print(f"Unique current employee IDs: {current['employee_id'].nunique()}")


if __name__ == "__main__":
    validate_employees()
