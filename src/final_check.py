
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

CLEAN_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
REPORT_FILE = ROOT / "reports" / "data_quality_report.xlsx"
REJECT_FILE = ROOT / "rejected" / "task_date_issues.csv"
PAYROLL_DQ_FILE = ROOT / "reports" / "payroll_dq_summary.csv"
PAYROLL_DETAIL_FILE = ROOT / "reports" / "payroll_exit_date_diagnostics.csv"


def show_check(name, count):
    status = "PASS" if count == 0 else "REVIEW REQUIRED"
    print(f"{name}: {count} affected records [{status}]")


def main():
    print("FINAL ETL PIPELINE CHECK")
    print("=" * 50)

    files = {
        "Cleaned dataset": CLEAN_FILE,
        "Data quality report": REPORT_FILE,
        "Rejected task records": REJECT_FILE,
        "Payroll DQ summary": PAYROLL_DQ_FILE,
        "Payroll diagnostic details": PAYROLL_DETAIL_FILE,
    }

    for name, path in files.items():
        status = "PASS" if path.exists() else "MISSING"
        print(f"{name}: {status}")

    if not CLEAN_FILE.exists():
        print("\nCannot continue: cleaned dataset is missing.")
        return

    # Check task data
    df = pd.read_excel(CLEAN_FILE, sheet_name="fact_task")

    print("\nTASK DATA QUALITY")
    print("-" * 50)
    print(f"Total task records: {len(df)}")

    show_check(
        "Duplicate task IDs",
        int(df["task_id"].duplicated().sum())
    )
    show_check(
        "Missing task IDs",
        int(df["task_id"].isna().sum())
    )
    show_check(
        "Missing assignees",
        int(df["assignee_employee_id"].isna().sum())
    )

    completed = pd.to_datetime(
        df["completed_date"], errors="coerce"
    )
    started = pd.to_datetime(
        df["started_date"], errors="coerce"
    )

    completed_before_start = (
        completed.notna()
        & started.notna()
        & (completed < started)
    )

    show_check(
        "Completed date before start date",
        int(completed_before_start.sum())
    )

    # Check previously generated payroll diagnostics
    if PAYROLL_DETAIL_FILE.exists():
        payroll = pd.read_csv(PAYROLL_DETAIL_FILE)

        print("\nPAYROLL DATA QUALITY")
        print("-" * 50)

        if "payroll_after_exit" in payroll.columns:
            after_exit = (
                payroll["payroll_after_exit"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("true")
            )
            show_check(
                "Payroll after employee exit date",
                int(after_exit.sum())
            )

        if "history_exists" in payroll.columns:
            missing_history = (
                payroll["history_exists"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("false")
            )
            show_check(
                "Payroll employees missing from dimension",
                int(missing_history.sum())
            )

    if PAYROLL_DQ_FILE.exists():
        summary = pd.read_csv(PAYROLL_DQ_FILE)

        print("\nDOCUMENTED PAYROLL ISSUES")
        print("-" * 50)

        for _, row in summary.iterrows():
            print(
                f"{row['check_name']}: "
                f"{row['affected_records']} records "
                f"[{row['severity']}]"
            )

    # Confirm the Excel report is readable
    if REPORT_FILE.exists():
        try:
            workbook = pd.ExcelFile(REPORT_FILE)
            print("\nREPORT WORKBOOK")
            print("-" * 50)
            print("Available sheets:", ", ".join(workbook.sheet_names))
        except Exception as exc:
            print(f"\nCould not read quality report: {exc}")

    print("\nFinal check completed.")
    print("Existing warehouse data was not modified by this script.")


if __name__ == "__main__":
    main()
