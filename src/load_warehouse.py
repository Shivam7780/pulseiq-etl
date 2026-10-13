
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILE = (
    ROOT / "data" / "raw"
    / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)

DB_URL = (
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

SCHEMA = "warehouse_v2"

# Excel source columns
SHEETS = {
    "dim_department": [
        "department_id", "department_name", "cost_center",
        "description", "is_leadership",
    ],
    "dim_role": [
        "role_id", "department_id", "role_title", "level",
        "grade", "band_min_annual", "band_mid_annual",
        "band_max_annual", "overtime_eligible",
        "band_reference_year",
    ],
    "dim_date": [
        "date", "date_key", "year", "quarter", "month_number",
        "month_name", "year_month", "week_of_year", "day_of_week",
        "is_weekend", "is_holiday", "is_working_day",
        "financial_year", "fiscal_quarter", "fiscal_month_number",
        "is_month_end", "month_start_date", "month_end_date",
    ],
    "dim_leave_type": [
        "leave_type_code", "leave_type_name", "pay_type",
        "annual_quota_days", "prorated_for_joiners",
        "carry_forward_allowed", "max_carry_forward_days",
        "policy_note",
    ],
    "dim_employee": [
        "employee_id", "full_name", "gender", "date_of_birth",
        "hire_date", "exit_date", "employment_status",
        "employment_type", "department_id", "role_id", "role_title",
        "job_level", "manager_id", "work_location", "work_mode",
        "highest_education", "valid_from", "valid_to", "is_current",
        "change_reason",
    ],
}

# Map Excel column names to actual PostgreSQL column names.
COLUMN_MAP = {
    "dim_role": {
        "level": "job_level",
    },
    "dim_date": {
        "date": "full_date",
        "year": "year_number",
        "quarter": "quarter_number",
    },
}


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found: {SOURCE_FILE}"
        )

    engine = create_engine(DB_URL)

    try:
        dataframes = {}

        # 1. Read and validate every source sheet.
        for table, source_columns in SHEETS.items():
            print(f"\nChecking source sheet: {table}")

            df = pd.read_excel(
                SOURCE_FILE,
                sheet_name=table,
            )
            df.columns = df.columns.astype(str).str.strip()

            missing = [
                col for col in source_columns
                if col not in df.columns
            ]

            if missing:
                raise ValueError(
                    f"{table}: missing Excel columns {missing}. "
                    f"Available columns: {df.columns.tolist()}"
                )

            df = df[source_columns].copy()

            # Rename columns to match the database schema.
            df = df.rename(
                columns=COLUMN_MAP.get(table, {})
            )

            # Convert missing values to Python None for SQL NULL.
            df = df.astype(object).where(pd.notna(df), None)

            dataframes[table] = df
            print(f"Validated {len(df)} rows.")

        # 2. Validate target tables and load everything atomically.
        with engine.begin() as conn:
            conn.execute(
                text(f'SET search_path TO "{SCHEMA}", public')
            )

            print("\nPostgreSQL connection successful.")

            for table, df in dataframes.items():
                result = conn.execute(
                    text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = :schema
                          AND table_name = :table
                        ORDER BY ordinal_position
                    """),
                    {"schema": SCHEMA, "table": table},
                )

                db_columns = [row[0] for row in result]

                if not db_columns:
                    raise RuntimeError(
                        f"Table {SCHEMA}.{table} does not exist."
                    )

                missing_db = [
                    col for col in df.columns
                    if col not in db_columns
                ]

                if missing_db:
                    raise ValueError(
                        f"{table}: database columns missing "
                        f"{missing_db}. Existing columns: {db_columns}"
                    )

                count = conn.execute(
                    text(
                        f'SELECT COUNT(*) FROM "{SCHEMA}"."{table}"'
                    )
                ).scalar_one()

                if count > 0:
                    raise RuntimeError(
                        f"{table} already contains {count} rows. "
                        "Loading stopped to prevent duplicate data."
                    )

            # Parent dimensions first, employee dimension last.
            load_order = [
                "dim_department",
                "dim_role",
                "dim_date",
                "dim_leave_type",
                "dim_employee",
            ]

            for table in load_order:
                df = dataframes[table]
                print(f"\nLoading {table}...")

                df.to_sql(
                    table,
                    con=conn,
                    schema=SCHEMA,
                    if_exists="append",
                    index=False,
                    chunksize=100,
                    method="multi",
                )

                actual_count = conn.execute(
                    text(
                        f'SELECT COUNT(*) FROM "{SCHEMA}"."{table}"'
                    )
                ).scalar_one()

                if actual_count != len(df):
                    raise RuntimeError(
                        f"{table}: expected {len(df)} rows, "
                        f"found {actual_count}."
                    )

                print(f"{table}: loaded {actual_count} rows.")

        print("\nSUCCESS: all five dimension tables loaded.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
