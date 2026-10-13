
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILE = (
    ROOT / "data" / "raw"
    / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)
CLEAN_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
REPORT_DIR = ROOT / "reports"
ISSUES_FILE = ROOT / "rejected" / "task_date_issues.csv"
PAYROLL_DQ_FILE = REPORT_DIR / "payroll_dq_summary.csv"
PAYROLL_DETAIL_FILE = REPORT_DIR / "payroll_exit_date_diagnostics.csv"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def status_for_count(count):
    return "PASS" if count == 0 else "REVIEW REQUIRED"


# ============================================================
# 1. TASK DATA QUALITY CHECKS
# ============================================================

tasks = pd.read_excel(CLEAN_FILE, sheet_name="fact_task")

completed = pd.to_datetime(tasks["completed_date"], errors="coerce")
started = pd.to_datetime(tasks["started_date"], errors="coerce")
created = pd.to_datetime(tasks["created_date"], errors="coerce")
due = pd.to_datetime(tasks["due_date"], errors="coerce")

task_status = tasks["status"].astype(str).str.strip().str.lower()

completed_before_started = int(
    (
        completed.notna()
        & started.notna()
        & (completed < started)
    ).sum()
)

done_without_date = int(
    (task_status.eq("done") & completed.isna()).sum()
)

task_checks = [
    ("Duplicate task IDs", int(tasks["task_id"].duplicated().sum())),
    ("Missing task IDs", int(tasks["task_id"].isna().sum())),
    (
        "Missing assignees",
        int(tasks["assignee_employee_id"].isna().sum()),
    ),
    (
        "Created date after due date",
        int(
            (
                created.notna()
                & due.notna()
                & (created > due)
            ).sum()
        ),
    ),
    (
        "Completed date before start date",
        completed_before_started,
    ),
    (
        "Done without completion date",
        done_without_date,
    ),
]

task_summary = pd.DataFrame([
    {
        "category": "Task",
        "check": name,
        "affected_records": count,
        "status": status_for_count(count),
    }
    for name, count in task_checks
])


# ============================================================
# 2. LEAVE DATA QUALITY CHECK: DQ-08
# ============================================================

leave = pd.read_excel(CLEAN_FILE, sheet_name="fact_leave")

leave_start = pd.to_datetime(leave["start_date"], errors="coerce")
leave_end = pd.to_datetime(leave["end_date"], errors="coerce")

invalid_leave_dates = (
    leave_start.notna()
    & leave_end.notna()
    & (leave_end < leave_start)
)

leave_end_before_start = int(invalid_leave_dates.sum())

leave_issues = leave.loc[invalid_leave_dates].copy()
leave_issues["issue_id"] = "DQ-08"
leave_issues["issue_type"] = "END_BEFORE_START"


# ============================================================
# 3. ATTRITION PREDICTION DATA QUALITY CHECK: DQ-09
# ============================================================

attrition = pd.read_excel(
    CLEAN_FILE,
    sheet_name="fact_attrition_risk",
)

attrition["as_of_date"] = pd.to_datetime(
    attrition["as_of_date"],
    errors="coerce",
)

latest_prediction_date = attrition["as_of_date"].max()

if pd.isna(latest_prediction_date):
    stale_prediction_mask = pd.Series(
        False, index=attrition.index
    )
    stale_prediction_cutoff = pd.NaT
else:
    stale_prediction_cutoff = (
        latest_prediction_date - pd.Timedelta(days=7)
    )
    stale_prediction_mask = (
        attrition["as_of_date"].notna()
        & (attrition["as_of_date"] < stale_prediction_cutoff)
    )

stale_prediction_count = int(stale_prediction_mask.sum())

stale_prediction_issues = attrition.loc[
    stale_prediction_mask
].copy()

stale_prediction_issues["issue_id"] = "DQ-09"
stale_prediction_issues["issue_type"] = "STALE_PREDICTION"


# ============================================================
# 4. EXISTING PAYROLL DIAGNOSTIC SUMMARY
# ============================================================

if PAYROLL_DQ_FILE.exists():
    payroll_source = pd.read_csv(PAYROLL_DQ_FILE)

    payroll_summary = pd.DataFrame({
        "category": "Payroll",
        "check": payroll_source["check_name"],
        "affected_records": pd.to_numeric(
            payroll_source["affected_records"],
            errors="coerce",
        ).fillna(0).astype(int),
    })

    payroll_summary["status"] = payroll_summary[
        "affected_records"
    ].apply(status_for_count)

    payroll_summary = payroll_summary[
        ["category", "check", "affected_records", "status"]
    ]
else:
    payroll_summary = pd.DataFrame(
        columns=[
            "category",
            "check",
            "affected_records",
            "status",
        ]
    )
    print("WARNING: Payroll DQ summary is missing.")


# ============================================================
# 5. COMBINE THE SUMMARY
# ============================================================

leave_summary = pd.DataFrame([{
    "category": "Leave",
    "check": "Leave end date before start date",
    "affected_records": leave_end_before_start,
    "status": status_for_count(leave_end_before_start),
}])

attrition_summary = pd.DataFrame([{
    "category": "Attrition",
    "check": "Stale attrition prediction",
    "affected_records": stale_prediction_count,
    "status": status_for_count(stale_prediction_count),
}])

summary = pd.concat(
    [
        task_summary,
        leave_summary,
        attrition_summary,
        payroll_summary,
    ],
    ignore_index=True,
)


# ============================================================
# 6. LOAD EXISTING ISSUE DETAILS
# ============================================================

if ISSUES_FILE.exists():
    task_issues = pd.read_csv(ISSUES_FILE)
else:
    task_issues = pd.DataFrame(
        columns=[
            "task_id",
            "status",
            "started_date",
            "completed_date",
        ]
    )

if PAYROLL_DETAIL_FILE.exists():
    payroll_details = pd.read_csv(PAYROLL_DETAIL_FILE)
else:
    payroll_details = pd.DataFrame()


# ============================================================
# 7. AUDIT THE 11 KNOWN ISSUES
# ============================================================

known_issues = pd.read_excel(
    SOURCE_FILE,
    sheet_name="dq_known_issues",
)

audit_map = {
    "DQ-01": (
        "Not verified",
        "Attendance after exit needs a dedicated DQ check.",
    ),
    "DQ-02": (
        "Not verified",
        "Payroll employee-month uniqueness needs a dedicated DQ check.",
    ),
    "DQ-03": (
        "Implemented",
        "Payroll diagnostics identify two missing employee references.",
    ),
    "DQ-04": (
        "Not verified",
        "Payroll-to-ledger reconciliation needs a dedicated DQ check.",
    ),
    "DQ-05": (
        "Not verified",
        "Invoice payment and balance rules need a dedicated DQ check.",
    ),
    "DQ-06": (
        "Implemented",
        "Task completed-before-start check is present.",
    ),
    "DQ-07": (
        "Implemented",
        "Done tasks without completion dates are checked against cleaned task data.",
    ),
    "DQ-08": (
        "Implemented",
        "Leave end-before-start check is measured from cleaned leave data.",
    ),
    "DQ-09": (
        "Implemented",
        "Predictions older than seven days before the latest prediction date are detected.",
    ),
    "DQ-10": (
        "Not verified",
        "Expense total reconciliation needs a dedicated DQ check.",
    ),
    "DQ-11": (
        "Not verified",
        "Employee history overlap needs a dedicated DQ check.",
    ),
}

known_issues["check_implementation_status"] = (
    known_issues["issue_id"].map(
        lambda issue_id: audit_map.get(
            issue_id, ("Not reviewed", "")
        )[0]
    )
)

known_issues["review_notes"] = known_issues["issue_id"].map(
    lambda issue_id: audit_map.get(
        issue_id, ("", "Review needed")
    )[1]
)

known_issues["detected_count_in_this_report"] = pd.NA
known_issues["detected_count_note"] = (
    "Not independently measured by this report"
)


def record_audit_count(issue_id, count, note):
    mask = known_issues["issue_id"].eq(issue_id)
    known_issues.loc[
        mask, "detected_count_in_this_report"
    ] = count
    known_issues.loc[
        mask, "detected_count_note"
    ] = note


record_audit_count(
    "DQ-03",
    2,
    "Two orphan payroll references confirmed by diagnostics",
)

record_audit_count(
    "DQ-06",
    completed_before_started,
    "Measured from cleaned task data",
)

record_audit_count(
    "DQ-07",
    done_without_date,
    "Measured from cleaned task data",
)

record_audit_count(
    "DQ-08",
    leave_end_before_start,
    "Measured from cleaned leave data",
)

record_audit_count(
    "DQ-09",
    stale_prediction_count,
    (
        f"Measured from cleaned data; latest date: "
        f"{latest_prediction_date.date()}, cutoff: "
        f"{stale_prediction_cutoff.date()}"
        if pd.notna(latest_prediction_date)
        else "No valid prediction dates were available"
    ),
)


# ============================================================
# 8. SAVE THE EXCEL REPORT
# ============================================================

output_file = REPORT_DIR / "data_quality_report.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    summary.to_excel(
        writer,
        sheet_name="Summary",
        index=False,
    )

    task_issues.to_excel(
        writer,
        sheet_name="Task Date Issues",
        index=False,
    )

    payroll_details.to_excel(
        writer,
        sheet_name="Payroll Issues",
        index=False,
    )

    known_issues.to_excel(
        writer,
        sheet_name="Known Issues Audit",
        index=False,
    )

    leave_issues.to_excel(
        writer,
        sheet_name="Leave Date Issues",
        index=False,
    )

    stale_prediction_issues.to_excel(
        writer,
        sheet_name="Stale Prediction Issues",
        index=False,
    )


# ============================================================
# 9. PRINT THE RESULTS
# ============================================================

print("DATA QUALITY REPORT")
print("=" * 55)
print(summary.to_string(index=False))

print("\nKNOWN ISSUES AUDIT")
print("=" * 55)
print(
    known_issues[
        [
            "issue_id",
            "issue_type",
            "check_implementation_status",
            "detected_count_in_this_report",
        ]
    ].to_string(index=False)
)

print("\nSTALE PREDICTION DETAILS")
print("=" * 55)
print("Latest prediction date:", latest_prediction_date)
print("Seven-day cutoff:", stale_prediction_cutoff)
print("Stale predictions:", stale_prediction_count)

if stale_prediction_issues.empty:
    print("No stale prediction records found.")
else:
    print(
        stale_prediction_issues[
            [
                "prediction_id",
                "employee_id",
                "as_of_date",
                "model_version",
            ]
        ].to_string(index=False)
    )

print(f"\nReport saved to: {output_file}")
