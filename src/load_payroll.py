
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)
REPORT_DIR = BASE_DIR / "reports"

DATABASE_URL = (
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

SCHEMA = "warehouse_v2"
TABLE = "fact_payroll"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# 2. Load and validate source data
# --------------------------------------------------
def main():
    print("Starting payroll ETL...")

    payroll = pd.read_excel(
        EXCEL_FILE,
        sheet_name="fact_payroll"
    )

    payroll.columns = (
        payroll.columns.str.strip().str.lower()
    )

    required_columns = [
        "payroll_item_id",
        "run_id",
        "employee_id",
        "period_end_date",
        "department_id",
        "role_id",
        "payable_days",
        "lop_days",
        "overtime_hours_paid",
        "variable_pay_type",
        "monthly_fixed_gross",
        "basic",
        "hra",
        "conveyance",
        "medical",
        "special_allowance",
        "earned_fixed_pay",
        "overtime_pay",
        "variable_pay",
        "gross_pay",
        "pf_employee",
        "esi_employee",
        "professional_tax",
        "tds",
        "other_deductions",
        "total_deductions",
        "net_pay",
        "pf_employer",
        "esi_employer",
        "employer_cost",
        "headcount_flag",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in payroll.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing source columns: {missing_columns}"
        )

    payroll["period_end_date"] = pd.to_datetime(
        payroll["period_end_date"],
        errors="coerce"
    ).dt.date

    invalid_dates = payroll["period_end_date"].isna()

    if invalid_dates.any():
        payroll.loc[invalid_dates].to_csv(
            REPORT_DIR / "invalid_payroll_dates.csv",
            index=False
        )
        raise ValueError(
            f"{int(invalid_dates.sum())} payroll rows have "
            "invalid period_end_date values. See "
            "reports/invalid_payroll_dates.csv."
        )

    payroll = payroll.drop_duplicates().copy()

    if payroll["payroll_item_id"].isna().any():
        raise ValueError(
            "Missing payroll_item_id values found."
        )

    if payroll["payroll_item_id"].duplicated().any():
        raise ValueError(
            "Duplicate payroll_item_id values found. "
            "Review the source data."
        )

    print(f"Source payroll rows: {len(payroll)}")

    # --------------------------------------------------
    # 3. Check target table before loading
    # --------------------------------------------------
    with engine.begin() as connection:
        existing_count = connection.execute(
            text(
                f"SELECT COUNT(*) FROM {SCHEMA}.{TABLE}"
            )
        ).scalar_one()

    if existing_count > 0:
        raise RuntimeError(
            f"{SCHEMA}.{TABLE} already contains "
            f"{existing_count} rows. Loading stopped "
            "to prevent duplicate data."
        )

    # --------------------------------------------------
    # 4. Read warehouse dimensions
    # --------------------------------------------------
    with engine.connect() as connection:
        employees = pd.read_sql(
            text("""
                SELECT
                    employee_key,
                    employee_id,
                    valid_from,
                    valid_to
                FROM warehouse_v2.dim_employee
            """),
            connection
        )

        dates = pd.read_sql(
            text("""
                SELECT
                    date_key AS warehouse_date_key,
                    full_date
                FROM warehouse_v2.dim_date
            """),
            connection
        )

    employees["valid_from"] = pd.to_datetime(
        employees["valid_from"],
        errors="coerce"
    ).dt.date

    employees["valid_to"] = pd.to_datetime(
        employees["valid_to"],
        errors="coerce"
    ).dt.date

    dates["full_date"] = pd.to_datetime(
        dates["full_date"],
        errors="coerce"
    ).dt.date

    # Remove source dimension keys. The warehouse keys
    # must come from the warehouse dimension tables.
    payroll_for_mapping = payroll.drop(
        columns=["employee_key", "date_key"],
        errors="ignore"
    ).copy()

    # --------------------------------------------------
    # 5. Map employees using effective date ranges
    # --------------------------------------------------
    mapped = payroll_for_mapping.merge(
        employees,
        on="employee_id",
        how="left",
        validate="many_to_many"
    )

    valid_employee = (
        mapped["employee_key"].notna()
        & mapped["valid_from"].notna()
        & (mapped["period_end_date"] >= mapped["valid_from"])
        & (
            mapped["valid_to"].isna()
            | (mapped["period_end_date"] <= mapped["valid_to"])
        )
    )

    mapped = mapped[valid_employee].copy()

    # Detect employee records that match more than one
    # historical dimension row.
    match_counts = mapped.groupby(
        "payroll_item_id"
    )["employee_key"].transform("count")

    ambiguous_ids = mapped.loc[
        match_counts > 1,
        "payroll_item_id"
    ].unique()

    ambiguous = mapped[
        mapped["payroll_item_id"].isin(ambiguous_ids)
    ].copy()

    if not ambiguous.empty:
        ambiguous.to_csv(
            REPORT_DIR / "ambiguous_payroll_employee_matches.csv",
            index=False
        )

    mapped = mapped[
        ~mapped["payroll_item_id"].isin(ambiguous_ids)
    ].copy()

    # --------------------------------------------------
    # 6. Map dates using the warehouse date dimension
    # --------------------------------------------------
    mapped = mapped.merge(
        dates,
        left_on="period_end_date",
        right_on="full_date",
        how="left",
        validate="many_to_one"
    )

    missing_dates = mapped["warehouse_date_key"].isna()

    if missing_dates.any():
        mapped.loc[missing_dates].to_csv(
            REPORT_DIR / "unmatched_payroll_dates.csv",
            index=False
        )

    # Identify all source records that cannot be loaded
    # because of employee matching or date matching.
    loadable_ids = set(
        mapped.loc[
            ~missing_dates,
            "payroll_item_id"
        ]
    )

    unmatched = payroll[
        ~payroll["payroll_item_id"].isin(loadable_ids)
    ].copy()

    unmatched.to_csv(
        REPORT_DIR / "unmatched_payroll.csv",
        index=False
    )

    ready = mapped[~missing_dates].copy()

    # --------------------------------------------------
    # 7. Prepare target columns
    # --------------------------------------------------
    ready["employee_key"] = ready[
        "employee_key"
    ].astype("int64")

    ready["date_key"] = ready[
        "warehouse_date_key"
    ].astype("int64")

    ready = ready.rename(
        columns={"basic": "basic_pay"}
    )

    target_columns = [
        "payroll_item_id",
        "run_id",
        "employee_key",
        "date_key",
        "period_end_date",
        "department_id",
        "role_id",
        "payable_days",
        "lop_days",
        "overtime_hours_paid",
        "variable_pay_type",
        "monthly_fixed_gross",
        "basic_pay",
        "hra",
        "conveyance",
        "medical",
        "special_allowance",
        "earned_fixed_pay",
        "overtime_pay",
        "variable_pay",
        "gross_pay",
        "pf_employee",
        "esi_employee",
        "professional_tax",
        "tds",
        "other_deductions",
        "total_deductions",
        "net_pay",
        "pf_employer",
        "esi_employer",
        "employer_cost",
        "headcount_flag",
    ]

    ready = ready[target_columns].copy()

    if ready["payroll_item_id"].duplicated().any():
        raise ValueError(
            "Duplicate payroll IDs remain after mapping."
        )

    if ready.empty:
        raise RuntimeError(
            "No payroll records can be loaded. "
            "Review the unmatched reports before proceeding."
        )

    # --------------------------------------------------
    # 8. Load payroll into PostgreSQL
    # --------------------------------------------------
    # Convert pandas missing values to SQL NULL.
    ready = ready.astype(object).where(pd.notna(ready), None)
    records = ready.to_dict(orient="records")

    # Upsert by the payroll business key. This keeps the load
    # repeatable without inserting duplicate payroll IDs.
    column_sql = ", ".join(f'"{col}"' for col in target_columns)
    placeholders = ", ".join(f":{col}" for col in target_columns)
    update_sql = ", ".join(
        f'"{col}" = EXCLUDED."{col}"'
        for col in target_columns
        if col != "payroll_item_id"
    )

    upsert_sql = text(
        f'INSERT INTO "{SCHEMA}"."{TABLE}" ({column_sql}) '
        f'VALUES ({placeholders}) '
        f'ON CONFLICT ("payroll_item_id") DO UPDATE SET {update_sql}'
    )

    # One transaction: any failed batch rolls back this load.
    with engine.begin() as connection:
        for start in range(0, len(records), 500):
            connection.execute(upsert_sql, records[start:start + 500])

        final_count = connection.execute(
            text(f'SELECT COUNT(*) FROM "{SCHEMA}"."{TABLE}"')
        ).scalar_one()

    print(f"Payroll rows processed: {len(records)}")
    print(f"Payroll rows in warehouse after load: {final_count}")

    print("\nPayroll ETL completed.")
    print(f"Source rows: {len(payroll)}")
    print(f"Loaded rows: {len(ready)}")
    print(f"Unmatched source rows: {len(unmatched)}")
    print(f"Ambiguous payroll IDs: {len(ambiguous_ids)}")
    print(
        "Unmatched report:",
        REPORT_DIR / "unmatched_payroll.csv"
    )

    if not ambiguous.empty:
        print(
            "Ambiguous matches report:",
            REPORT_DIR / "ambiguous_payroll_employee_matches.csv"
        )

    if missing_dates.any():
        print(
            "Rows missing a warehouse date:",
            int(missing_dates.sum()),
            "- see reports/unmatched_payroll_dates.csv"
        )

    print("Next, verify the database row count.")


if __name__ == "__main__":
    main()
