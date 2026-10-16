import pandas as pd
from sqlalchemy import create_engine, text

WORKBOOK = "data/clean/pulseiq_cleaned.xlsx"
DB_URL = (
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

engine = create_engine(DB_URL, future=True)

# Source sheet, destination table, and conflict key.
TABLES = [
    ("dim_department", "dim_department", ["department_id"]),
    ("dim_role", "dim_role", ["role_id"]),
    ("dim_date", "dim_date", ["date_key"]),
    ("dim_leave_type", "dim_leave_type", ["leave_type_code"]),
    ("dim_employee", "dim_employee", ["employee_key"]),
    ("fact_payroll", "fact_payroll", ["payroll_item_id"]),
    ("fact_attendance_monthly", "fact_attendance_monthly", ["attendance_fact_id"]),
    ("fact_leave", "fact_leave", ["leave_request_id"]),
    ("fact_headcount_monthly", "fact_headcount_monthly", ["date_key", "department_id"]),
]

RENAMES = {
    "dim_date": {
        "date": "full_date",
        "year": "year_number",
        "quarter": "quarter_number",
    },
    "dim_role": {"level": "job_level"},
    "fact_payroll": {"basic": "basic_pay"},
}

# The source workbook stores boolean fields as Y/N.
BOOLEAN_COLUMNS = {
    "is_current", "is_leadership", "overtime_eligible",
    "is_weekend", "is_holiday", "is_working_day", "is_month_end",
    "prorated_for_joiners", "carry_forward_allowed",
}

def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return value

def load_table(sheet, table, keys):
    df = pd.read_excel(WORKBOOK, sheet_name=sheet)
    df = df.rename(columns=RENAMES.get(sheet, {}))

    # Employee IDs in the fact sheets are descriptive source fields;
    # the warehouse facts use the version-specific employee_key.
    if table.startswith("fact_") and "employee_id" in df.columns:
        df = df.drop(columns=["employee_id"])

    # The target schema uses basic_pay, while the source uses basic.
    with engine.begin() as conn:
        if table in ("fact_payroll", "fact_attendance_monthly", "fact_leave"):
            valid_keys = set(
                conn.execute(text("SELECT employee_key FROM dw.dim_employee"))
                .scalars()
                .all()
            )
            if "employee_key" in df.columns:
                before = len(df)
                df = df[df["employee_key"].isin(valid_keys)].copy()
                skipped = before - len(df)
                if skipped:
                    print(f"{table}: skipped {skipped} rows with unknown employee keys")

        if df.empty:
            print(f"{table}: no rows to load")
            return

        columns = list(df.columns)
        for col in columns:
            if col in BOOLEAN_COLUMNS:
                df[col] = df[col].map(
                    lambda v: (
                        None if pd.isna(v)
                        else v if isinstance(v, bool)
                        else str(v).strip().upper() in ("Y", "YES", "TRUE", "1")
                    )
                )

        columns_sql = ", ".join(f'"{c}"' for c in columns)
        placeholders = ", ".join(f":{c}" for c in columns)
        conflict_sql = ", ".join(f'"{c}"' for c in keys)
        updates = [c for c in columns if c not in keys]

        if updates:
            update_sql = ", ".join(
                f'"{c}" = EXCLUDED."{c}"' for c in updates
            )
            upsert = (
                f'INSERT INTO dw."{table}" ({columns_sql}) '
                f'VALUES ({placeholders}) '
                f'ON CONFLICT ({conflict_sql}) DO UPDATE SET {update_sql}'
            )
        else:
            upsert = (
                f'INSERT INTO dw."{table}" ({columns_sql}) '
                f'VALUES ({placeholders}) '
                f'ON CONFLICT ({conflict_sql}) DO NOTHING'
            )

        records = []
        for row in df.to_dict(orient="records"):
            records.append({k: clean_value(v) for k, v in row.items()})

        conn.execute(text(upsert), records)

        count = conn.execute(
            text(f'SELECT COUNT(*) FROM dw."{table}"')
        ).scalar_one()

    print(f"dw.{table}: processed {len(records)} rows; table now has {count}")

def main():
    for sheet, table, keys in TABLES:
        load_table(sheet, table, keys)

    print("\nWarehouse load completed.")

if __name__ == "__main__":
    main()
