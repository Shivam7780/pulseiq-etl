
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
SOURCE_SHEET = "fact_attendance_monthly"
TARGET_TABLE = "fact_attendance"

COLUMNS = [
    "attendance_fact_id",
    "employee_id",
    "date_key",
    "department_id",
    "scheduled_days",
    "present_days",
    "wfh_days",
    "half_days_unpaid",
    "paid_leave_days",
    "unpaid_absence_days",
    "late_arrivals",
    "avg_hours_worked",
    "overtime_hours",
    "attendance_rate",
    "period_end_date",
]


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(SOURCE_FILE)

    df = pd.read_excel(SOURCE_FILE, sheet_name=SOURCE_SHEET)
    df.columns = df.columns.astype(str).str.strip()

    missing = [column for column in COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing source columns: {missing}")

    df = df[COLUMNS].copy()
    df["period_end_date"] = pd.to_datetime(
        df["period_end_date"], errors="coerce"
    )

    if df["attendance_fact_id"].isna().any():
        raise ValueError("Attendance IDs contain missing values.")

    if df["attendance_fact_id"].duplicated().any():
        raise ValueError("Duplicate attendance IDs found.")

    if df[["employee_id", "date_key", "period_end_date"]].isna().any().any():
        raise ValueError(
            "Missing employee IDs, date keys, or period-end dates found."
        )

    engine = create_engine(DB_URL)

    try:
        # Read the full employee history dimension.
        employees = pd.read_sql(
            text("""
                SELECT employee_key, employee_id, valid_from, valid_to
                FROM warehouse_v2.dim_employee
            """),
            engine,
        )

        employees["valid_from"] = pd.to_datetime(employees["valid_from"])
        employees["valid_to"] = pd.to_datetime(employees["valid_to"])

        # Match employee ID first, then validate the date against history.
        matched = df.merge(
            employees,
            on="employee_id",
            how="left",
            suffixes=("", "_dimension"),
        )

        valid = (
            matched["employee_key"].notna()
            & matched["period_end_date"].ge(matched["valid_from"])
            & matched["period_end_date"].le(matched["valid_to"])
        )

        valid_matches = matched.loc[valid].copy()

        # Each attendance record must match exactly one dimension version.
        match_counts = valid_matches.groupby(
            "attendance_fact_id"
        ).size()

        duplicate_ids = match_counts[match_counts > 1].index
        if len(duplicate_ids):
            raise ValueError(
                "Multiple employee-history matches found for attendance IDs: "
                f"{list(duplicate_ids[:10])}"
            )

        matched_ids = set(valid_matches["attendance_fact_id"])
        unmatched = df.loc[
            ~df["attendance_fact_id"].isin(matched_ids)
        ].copy()

        unmatched_path = ROOT / "reports" / "unmatched_attendance.csv"
        unmatched_path.parent.mkdir(parents=True, exist_ok=True)
        unmatched.to_csv(unmatched_path, index=False)

        print(f"Total attendance rows: {len(df)}")
        print(f"Matched attendance rows: {len(valid_matches)}")
        print(f"Unmatched attendance rows: {len(unmatched)}")
        print(f"Unmatched records saved to: {unmatched_path}")

        if unmatched.empty:
            print("All attendance rows have valid employee-history matches.")
        else:
            print(
                "Review unmatched records before deciding whether they "
                "should be excluded or whether dimension history needs repair."
            )

        # Use the warehouse surrogate key, not the source employee key.
        load_df = valid_matches[COLUMNS + ["employee_key"]].copy()
        load_df = load_df.rename(
            columns={"employee_key": "warehouse_employee_key"}
        )

        # Map the dimension key into the target table's employee_key column.
        load_df["employee_key"] = load_df.pop("warehouse_employee_key")
        load_df = load_df[
            [
                "attendance_fact_id",
                "employee_key",
                "date_key",
                "department_id",
                "scheduled_days",
                "present_days",
                "wfh_days",
                "half_days_unpaid",
                "paid_leave_days",
                "unpaid_absence_days",
                "late_arrivals",
                "avg_hours_worked",
                "overtime_hours",
                "attendance_rate",
                "period_end_date",
            ]
        ]

        load_df = load_df.astype(object).where(pd.notna(load_df), None)

        # Prepare records for a repeatable PostgreSQL upsert.
        load_df = load_df.astype(object).where(pd.notna(load_df), None)
        records = load_df.to_dict(orient="records")
        target_columns = list(load_df.columns)

        if "attendance_fact_id" not in target_columns:
            raise RuntimeError(
                "attendance_fact_id is missing from the load columns."
            )

        column_sql = ", ".join(f'"{col}"' for col in target_columns)
        placeholders = ", ".join(f":{col}" for col in target_columns)
        update_sql = ", ".join(
            f'"{col}" = EXCLUDED."{col}"'
            for col in target_columns
            if col != "attendance_fact_id"
        )

        upsert_sql = text(
            f'INSERT INTO "{SCHEMA}"."{TARGET_TABLE}" ({column_sql}) '
            f'VALUES ({placeholders}) '
            f'ON CONFLICT ("attendance_fact_id") DO UPDATE SET {update_sql}'
        )

        # One transaction protects the entire load from partial updates.
        with engine.begin() as conn:
            for start in range(0, len(records), 500):
                conn.execute(upsert_sql, records[start:start + 500])

            final_count = conn.execute(
                text(
                    f'SELECT COUNT(*) FROM "{SCHEMA}"."{TARGET_TABLE}"'
                )
            ).scalar_one()

        print(f"Attendance rows processed: {len(records)}")
        print(f"Attendance rows in warehouse after load: {final_count}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
