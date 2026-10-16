
import os
import pandas as pd
from sqlalchemy import create_engine, text

FILE_PATH = "data/clean/pulseiq_cleaned.xlsx"
SHEET_NAME = "fact_leave"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL before running this loader.")

COLUMNS = [
    "leave_request_id", "employee_key", "leave_type_code",
    "start_date_key", "end_date_key", "start_date", "end_date",
    "days", "status", "applied_on", "decided_on", "approver_id", "reason",
]


def main():
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["leave_type_code"] = df["leave_type_code"].astype("string").str.strip()

    # Keep the original employee_id for historical employee mapping.
    df = df.drop(columns=["employee_key"])

    engine = create_engine(DATABASE_URL)

    try:
        with engine.begin() as conn:
            employees = pd.read_sql(text("""
                SELECT employee_id, employee_key, valid_from, valid_to
                FROM warehouse_v2.dim_employee
            """), conn)

            leave_types = set(conn.execute(text(
                "SELECT leave_type_code FROM warehouse_v2.dim_leave_type"
            )).scalars().all())

            employees["valid_from"] = pd.to_datetime(employees["valid_from"])
            employees["valid_to"] = pd.to_datetime(employees["valid_to"])

            mapped = df.merge(employees, on="employee_id", how="left")

            valid_employee = (
                mapped["start_date"].notna()
                & mapped["valid_from"].notna()
                & mapped["valid_to"].notna()
                & (mapped["valid_from"] <= mapped["start_date"])
                & (mapped["valid_to"] >= mapped["start_date"])
            )

            mapped = mapped.loc[valid_employee].copy()

            counts = mapped.groupby("leave_request_id")["employee_key"].transform(
                "nunique"
            )
            mapped = mapped.loc[counts == 1].copy()
            mapped["employee_key"] = mapped["employee_key"].astype("int64")

            valid = mapped[mapped["leave_type_code"].isin(leave_types)].copy()
            valid = valid[COLUMNS].copy()
            valid = valid.astype(object).where(pd.notna(valid), None)

            if valid["leave_request_id"].duplicated().any():
                raise RuntimeError("Duplicate leave request IDs found; stopping.")

            valid_ids = set(valid["leave_request_id"])
            rejected = df[~df["leave_request_id"].isin(valid_ids)].copy()

            if not rejected.empty:
                os.makedirs("rejected", exist_ok=True)
                rejected.to_csv("rejected/leave_fk_rejected.csv", index=False)

            if not valid.empty:
                columns_sql = ", ".join(f'"{c}"' for c in COLUMNS)
                values_sql = ", ".join(f":{c}" for c in COLUMNS)
                updates_sql = ", ".join(
                    f'"{c}" = EXCLUDED."{c}"'
                    for c in COLUMNS
                    if c != "leave_request_id"
                )

                statement = text(f"""
                    INSERT INTO warehouse_v2.fact_leave ({columns_sql})
                    VALUES ({values_sql})
                    ON CONFLICT ("leave_request_id")
                    DO UPDATE SET {updates_sql}
                """)

                records = valid.to_dict(orient="records")
                for start in range(0, len(records), 250):
                    conn.execute(statement, records[start:start + 250])

            final_count = conn.execute(text(
                "SELECT COUNT(*) FROM warehouse_v2.fact_leave"
            )).scalar()

            print(f"Source rows: {len(df)}")
            print(f"Valid rows processed: {len(valid)}")
            print(f"Rows rejected: {len(rejected)}")
            print(f"Final fact_leave count: {final_count}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
