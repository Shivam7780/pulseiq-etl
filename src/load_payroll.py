
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

    payroll.columns = payroll.columns.str.strip().str.lower()

    required_columns = [
        "payroll_item_id", "run_id", "employee_id",
        "employee_key", "period_end_date", "department_id",
        "role_id", "payable_days", "lop_days",
        "overtime_hours_paid", "variable_pay_type",
        "monthly_fixed_gross", "basic", "hra", "conveyance",
        "medical", "special_allowance", "earned_fixed_pay",
        "overtime_pay", "variable_pay", "gross_pay",
        "pf_employee", "esi_employee", "professional_tax",
        "tds", "other_deductions", "total_deductions",
        "net_pay", "pf_employer", "esi_employer",
        "employer_cost", "headcount_flag",
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
        payroll["period_end_date"], errors="coerce"
    ).dt.date

    invalid_dates = payroll["period_end_date"].isna()
    if invalid_dates.any():
        payroll.loc[invalid_dates].to_csv(
            REPORT_DIR / "invalid_payroll_dates.csv",
            index=False
        )
        raise ValueError(
            f"{int(invalid_dates.sum())} payroll rows have invalid dates."
        )

    payroll = payroll.drop_duplicates().copy()

    if payroll["payroll_item_id"].isna().any():
        raise ValueError("Missing payroll_item_id values.")

    if payroll["payroll_item_id"].duplicated().any():
        raise ValueError("Duplicate payroll_item_id values in source.")

    payroll["employee_key"] = pd.to_numeric(
        payroll["employee_key"], errors="coerce"
    ).astype("Int64")

    print(f"Source payroll rows: {len(payroll)}")

    # --------------------------------------------------
    # 3. Existing rows are handled by the upsert below
    # --------------------------------------------------

    # --------------------------------------------------
    # 4. Read warehouse dimensions
    # --------------------------------------------------
    with engine.connect() as connection:
        employees = pd.read_sql(
            text("""
                SELECT employee_key, employee_id, valid_from, valid_to
                FROM warehouse_v2.dim_employee
            """),
            connection
        )

        dates = pd.read_sql(
            text("""
                SELECT date_key AS warehouse_date_key, full_date
                FROM warehouse_v2.dim_date
            """),
            connection
        )

    employees["valid_from"] = pd.to_datetime(
        employees["valid_from"], errors="coerce"
    ).dt.date

    employees["valid_to"] = pd.to_datetime(
        employees["valid_to"], errors="coerce"
    ).dt.date

    dates["full_date"] = pd.to_datetime(
        dates["full_date"], errors="coerce"
    ).dt.date

    # Keep the source employee key to identify the correct history row.
    payroll_for_mapping = payroll.drop(
        columns=["date_key"], errors="ignore"
    ).rename(
        columns={"employee_key": "source_employee_key"}
    ).copy()

    # --------------------------------------------------
    # 5. Map source employee versions to warehouse keys
    # --------------------------------------------------
    source_employees = pd.read_excel(
        EXCEL_FILE,
        sheet_name="dim_employee"
    )

    source_employees.columns = (
        source_employees.columns.str.strip().str.lower()
    )

    source_required = ["employee_key", "employee_id", "valid_from"]
    missing_source_columns = [
        col for col in source_required
        if col not in source_employees.columns
    ]
    if missing_source_columns:
        raise ValueError(
            f"Missing source employee columns: {missing_source_columns}"
        )

    source_employees = source_employees[
        ["employee_key", "employee_id", "valid_from"]
    ].drop_duplicates().rename(
        columns={"employee_key": "source_employee_key"}
    )

    source_employees["source_employee_key"] = pd.to_numeric(
        source_employees["source_employee_key"], errors="coerce"
    ).astype("Int64")

    source_employees["valid_from"] = pd.to_datetime(
        source_employees["valid_from"], errors="coerce"
    ).dt.date

    if source_employees["source_employee_key"].duplicated().any():
        source_employees.loc[
            source_employees["source_employee_key"].duplicated(
                keep=False
            )
        ].to_csv(
            REPORT_DIR / "duplicate_source_employee_keys.csv",
            index=False
        )
        raise ValueError(
            "Duplicate source employee keys found. Check reports."
        )

    # Each payroll item must identify its source employee version.
    mapped = payroll_for_mapping.merge(
        source_employees,
        on=["source_employee_key", "employee_id"],
        how="left",
        validate="many_to_one"
    )

    # Map the source version to the warehouse surrogate key.
    warehouse_employees = employees[
        ["employee_key", "employee_id", "valid_from"]
    ].rename(
        columns={"employee_key": "warehouse_employee_key"}
    )

    if warehouse_employees.duplicated(
        subset=["employee_id", "valid_from"]
    ).any():
        warehouse_employees.loc[
            warehouse_employees.duplicated(
                subset=["employee_id", "valid_from"],
                keep=False
            )
        ].to_csv(
            REPORT_DIR / "duplicate_warehouse_employee_versions.csv",
            index=False
        )
        raise ValueError(
            "Duplicate warehouse employee versions found."
        )

    mapped = mapped.merge(
        warehouse_employees,
        on=["employee_id", "valid_from"],
        how="left",
        validate="many_to_one"
    )

    missing_employee_map = mapped["warehouse_employee_key"].isna()

    if missing_employee_map.any():
        mapped.loc[missing_employee_map].to_csv(
            REPORT_DIR / "unmatched_payroll_employee_mapping.csv",
            index=False
        )

    mapped = mapped.loc[~missing_employee_map].copy()
    mapped["employee_key"] = (
        mapped["warehouse_employee_key"].astype("int64")
    )

    # Remove any payroll item that maps more than once.
    match_counts = mapped.groupby(
        "payroll_item_id"
    )["employee_key"].transform("count")

    ambiguous_ids = mapped.loc[
        match_counts > 1, "payroll_item_id"
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

    loadable_ids = set(
        mapped.loc[~missing_dates, "payroll_item_id"]
    )

    unmatched = payroll[
        ~payroll["payroll_item_id"].isin(loadable_ids)
    ].copy()

    unmatched.to_csv(
        REPORT_DIR / "unmatched_payroll.csv",
        index=False
    )

    ready = mapped.loc[~missing_dates].copy()

    # --------------------------------------------------
    # 7. Prepare target columns
    # --------------------------------------------------
    ready["employee_key"] = ready["employee_key"].astype("int64")
    ready["date_key"] = ready["warehouse_date_key"].astype("int64")

    ready = ready.rename(columns={"basic": "basic_pay"})

    target_columns = [
        "payroll_item_id", "run_id", "employee_key", "date_key",
        "period_end_date", "department_id", "role_id",
        "payable_days", "lop_days", "overtime_hours_paid",
        "variable_pay_type", "monthly_fixed_gross", "basic_pay",
        "hra", "conveyance", "medical", "special_allowance",
        "earned_fixed_pay", "overtime_pay", "variable_pay",
        "gross_pay", "pf_employee", "esi_employee",
        "professional_tax", "tds", "other_deductions",
        "total_deductions", "net_pay", "pf_employer",
        "esi_employer", "employer_cost", "headcount_flag",
    ]

    missing_target_columns = [
        col for col in target_columns
        if col not in ready.columns
    ]
    if missing_target_columns:
        raise ValueError(
            f"Missing target columns: {missing_target_columns}"
        )

    ready = ready[target_columns].copy()

    if ready["payroll_item_id"].duplicated().any():
        ready.loc[
            ready["payroll_item_id"].duplicated(keep=False)
        ].to_csv(
            REPORT_DIR / "duplicate_mapped_payroll_items.csv",
            index=False
        )
        raise ValueError(
            "Duplicate payroll IDs remain after mapping."
        )

    if ready.empty:
        raise RuntimeError(
            "No payroll records can be loaded. Review unmatched reports."
        )

    # --------------------------------------------------
    # 8. Upsert payroll into PostgreSQL
    # --------------------------------------------------
    ready = ready.astype(object).where(pd.notna(ready), None)
    records = ready.to_dict(orient="records")

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

    # Transaction ensures the batch is committed together.
    with engine.begin() as connection:
        for start in range(0, len(records), 500):
            connection.execute(
                upsert_sql,
                records[start:start + 500]
            )

        final_count = connection.execute(
            text(f'SELECT COUNT(*) FROM "{SCHEMA}"."{TABLE}"')
        ).scalar_one()

    print(f"Payroll rows processed: {len(records)}")
    print(f"Payroll rows in warehouse after load: {final_count}")
    print(f"Source rows: {len(payroll)}")
    print(f"Loaded rows: {len(ready)}")
    print(f"Unmatched source rows: {len(unmatched)}")
    print(f"Ambiguous payroll IDs: {len(ambiguous_ids)}")
    print("Unmatched report:", REPORT_DIR / "unmatched_payroll.csv")
    print("Payroll ETL completed. Verify totals against the answer key.")


if __name__ == "__main__":
    main()
