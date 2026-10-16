
import pandas as pd
from sqlalchemy import create_engine

# --------------------------------------------------
# 1. Database connection
# --------------------------------------------------
engine = create_engine(
    "postgresql+psycopg2://pulseiq_user:"
    "pulseiq_dev_password@localhost:5432/pulseiq_warehouse"
)

# --------------------------------------------------
# 2. Load unmatched payroll records
# --------------------------------------------------
unmatched = pd.read_csv(
    "reports/unmatched_payroll.csv"
)

unmatched["period_end_date"] = pd.to_datetime(
    unmatched["period_end_date"],
    errors="coerce"
)

# Remove source keys so we use warehouse keys.
unmatched = unmatched.drop(
    columns=["employee_key", "date_key"],
    errors="ignore"
)

# --------------------------------------------------
# 3. Load employee dimension history
# --------------------------------------------------
with engine.connect() as connection:
    employees = pd.read_sql(
        """
        SELECT
            employee_id,
            employee_key,
            valid_from,
            valid_to,
            is_current
        FROM warehouse_v2.dim_employee
        """,
        connection
    )

employees["valid_from"] = pd.to_datetime(
    employees["valid_from"],
    errors="coerce"
)

employees["valid_to"] = pd.to_datetime(
    employees["valid_to"],
    errors="coerce"
)

# --------------------------------------------------
# 4. Match employee IDs to their history
# --------------------------------------------------
merged = unmatched.merge(
    employees,
    on="employee_id",
    how="left",
    validate="many_to_many"
)

has_history = merged["employee_key"].notna()

date_matches = (
    has_history
    & merged["valid_from"].notna()
    & (
        merged["period_end_date"]
        >= merged["valid_from"]
    )
    & (
        merged["valid_to"].isna()
        | (
            merged["period_end_date"]
            <= merged["valid_to"]
        )
    )
)

# Count unique payroll records in each category.
no_history_ids = merged.loc[
    ~has_history, "payroll_item_id"
].nunique()

no_valid_date_ids = merged.loc[
    has_history & ~date_matches, "payroll_item_id"
].nunique()

valid_match_ids = merged.loc[
    date_matches, "payroll_item_id"
].nunique()

print("\n===== PAYROLL DIAGNOSTIC RESULTS =====")
print("Unmatched source rows:", len(unmatched))
print("Rows with no employee history:", no_history_ids)
print(
    "Rows with history but no valid date match:",
    no_valid_date_ids
)
print("Rows with a valid history match:", valid_match_ids)

# --------------------------------------------------
# 5. Display sample records needing investigation
# --------------------------------------------------
print("\n===== FIRST 15 RECORDS WITHOUT A VALID MATCH =====")

problem_rows = merged.loc[
    ~date_matches,
    [
        "employee_id",
        "payroll_item_id",
        "period_end_date",
        "employee_key",
        "valid_from",
        "valid_to",
        "is_current"
    ]
].drop_duplicates(
    subset=["employee_id", "payroll_item_id"]
)

print(
    problem_rows.head(15).to_string(index=False)
)

# Save the diagnostic results for review.
problem_rows.to_csv(
    "reports/payroll_history_diagnostics.csv",
    index=False
)

print(
    "\nDiagnostic report saved to "
    "reports/payroll_history_diagnostics.csv"
)

# --------------------------------------------------
# 6. Check all historical versions for a valid match
# --------------------------------------------------
valid_history_ids = merged.loc[
    date_matches, "payroll_item_id"
].unique()

all_payroll_ids = unmatched["payroll_item_id"].unique()

valid_id_set = set(valid_history_ids)

still_unmatched_ids = [
    payroll_id
    for payroll_id in all_payroll_ids
    if payroll_id not in valid_id_set
]

print("\n===== FINAL HISTORY MATCH CHECK =====")
print("Source payroll IDs:", len(all_payroll_ids))
print("IDs with a valid history match:", len(valid_id_set))
print("IDs without a valid history match:", len(still_unmatched_ids))

# Show all available history versions for the first
# five unmatched payroll records.
sample_ids = still_unmatched_ids[:5]

print("\n===== ALL HISTORY VERSIONS FOR SAMPLE RECORDS =====")
print(
    merged.loc[
        merged["payroll_item_id"].isin(sample_ids),
        [
            "employee_id",
            "payroll_item_id",
            "period_end_date",
            "employee_key",
            "valid_from",
            "valid_to",
            "is_current"
        ]
    ].sort_values(
        ["payroll_item_id", "valid_from"]
    ).to_string(index=False)
)
