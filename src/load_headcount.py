from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SOURCE_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
SCHEMA = "warehouse_v2"
TABLE = "fact_headcount_monthly"

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is missing from the project .env file")

COLUMNS = [
    "date_key",
    "month_start_date",
    "department_id",
    "headcount_start",
    "hires",
    "exits",
    "voluntary_exits",
    "transfers_in",
    "transfers_out",
    "headcount_end",
    "attrition_rate_monthly_pct",
]


def main():
    df = pd.read_excel(
        SOURCE_FILE,
        sheet_name=TABLE,
    )

    df.columns = df.columns.astype(str).str.strip()
    df = df[COLUMNS].copy()

    if df[["date_key", "month_start_date", "department_id"]].isna().any().any():
        raise ValueError("Required headcount keys or dates contain missing values.")

    if df.duplicated(["date_key", "department_id"]).any():
        raise ValueError("Duplicate (date_key, department_id) keys found.")

    df["date_key"] = df["date_key"].astype(int)
    df["month_start_date"] = pd.to_datetime(
        df["month_start_date"]
    ).dt.date

    df = df.astype(object).where(pd.notna(df), None)

    insert_sql = text("""
        INSERT INTO warehouse_v2.fact_headcount_monthly (
            date_key,
            month_start_date,
            department_id,
            headcount_start,
            hires,
            exits,
            voluntary_exits,
            transfers_in,
            transfers_out,
            headcount_end,
            attrition_rate_monthly_pct
        )
        VALUES (
            :date_key,
            :month_start_date,
            :department_id,
            :headcount_start,
            :hires,
            :exits,
            :voluntary_exits,
            :transfers_in,
            :transfers_out,
            :headcount_end,
            :attrition_rate_monthly_pct
        )
        ON CONFLICT (date_key, department_id)
        DO UPDATE SET
            month_start_date = EXCLUDED.month_start_date,
            headcount_start = EXCLUDED.headcount_start,
            hires = EXCLUDED.hires,
            exits = EXCLUDED.exits,
            voluntary_exits = EXCLUDED.voluntary_exits,
            transfers_in = EXCLUDED.transfers_in,
            transfers_out = EXCLUDED.transfers_out,
            headcount_end = EXCLUDED.headcount_end,
            attrition_rate_monthly_pct =
                EXCLUDED.attrition_rate_monthly_pct
    """)

    engine = create_engine(DB_URL)

    try:
        with engine.begin() as conn:
            conn.execute(
                text("SELECT set_config('search_path', :path, true)"),
                {"path": f"{SCHEMA},public"},
            )
            # Check date dimension references before loading.
            available_dates = {
                row[0]
                for row in conn.execute(text(
                    "SELECT date_key FROM warehouse_v2.dim_date"
                ))
            }
            unavailable = sorted(
                set(df["date_key"].astype(int)) - available_dates
            )
            if unavailable:
                raise ValueError(
                    f"{len(unavailable)} date keys are missing from "
                    f"warehouse_v2.dim_date. Sample: {unavailable[:10]}"
                )

            available_departments = {
                row[0]
                for row in conn.execute(text(
                    "SELECT department_id FROM warehouse_v2.dim_department"
                ))
            }
            unknown_departments = sorted(
                set(df["department_id"].astype(str)) - available_departments
            )
            if unknown_departments:
                raise ValueError(
                    "Department IDs missing from dim_department: "
                    f"{unknown_departments}"
                )

            conn.execute(insert_sql, df.to_dict(orient="records"))

            final_count = conn.execute(text(
                "SELECT COUNT(*) "
                "FROM warehouse_v2.fact_headcount_monthly"
            )).scalar_one()

        print(f"Source records processed: {len(df)}")
        print(f"Headcount rows now in database: {final_count}")
        print("Headcount upsert completed successfully.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
