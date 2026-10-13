import pandas as pd
import pandera.pandas as pa


def validate_employee_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate employee IDs and date columns."""

    df = df.copy()

    required = {"employee_id"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df["employee_id"].isna().any():
        raise ValueError("Validation failed: missing employee IDs")

    if df["employee_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Validation failed: blank employee IDs")

    # Historical employee records can share an ID.
    # Only current employee IDs must be unique.
    if "is_current" in df.columns:
        current = df["is_current"].astype(str).str.strip().str.upper().eq("Y")
        current_ids = df.loc[current, "employee_id"].astype(str).str.strip()

        if current_ids.duplicated().any():
            raise ValueError("Validation failed: duplicate current employee IDs")

    for column in ("hire_date", "joining_date", "leaving_date", "exit_date"):
        if column in df.columns:
            original = df[column]
            parsed = pd.to_datetime(original, errors="coerce")
            invalid = original.notna() & parsed.isna()

            if invalid.any():
                raise ValueError(
                    f"Validation failed: {int(invalid.sum())} invalid dates in {column}"
                )

            df[column] = parsed

    if "salary" in df.columns:
        df["salary"] = pd.to_numeric(df["salary"], errors="raise")

        if (df["salary"].dropna() < 0).any():
            raise ValueError("Validation failed: negative salaries found")

    return df


if __name__ == "__main__":
    from pathlib import Path

    path = Path("data/clean/pulseiq_cleaned.xlsx")
    employees = pd.read_excel(path, sheet_name="dim_employee")

    validated = validate_employee_data(employees)

    print("EMPLOYEE PANDERA VALIDATION PASSED")
    print(f"Rows validated: {len(validated)}")
    print(f"Current employee rows: {(validated['is_current'].astype(str).str.strip().str.upper() == 'Y').sum()}")