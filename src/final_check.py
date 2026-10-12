
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

CLEAN_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
REPORT_FILE = ROOT / "reports" / "data_quality_report.xlsx"
REJECT_FILE = ROOT / "rejected" / "task_date_issues.csv"

def main():
    print("FINAL ETL PIPELINE CHECK")
    print("=" * 40)

    # Check required output files
    files = {
        "Cleaned dataset": CLEAN_FILE,
        "Data quality report": REPORT_FILE,
        "Rejected records": REJECT_FILE,
    }

    for name, path in files.items():
        status = "PASS" if path.exists() else "MISSING"
        print(f"{name}: {status}")

    if not CLEAN_FILE.exists() or not REPORT_FILE.exists():
        print("\nFix missing output files before proceeding.")
        return

    # Verify cleaned task data
    df = pd.read_excel(CLEAN_FILE, sheet_name="fact_task")

    print(f"\nTotal task records: {len(df)}")
    print(f"Duplicate task IDs: {df['task_id'].duplicated().sum()}")
    print(f"Missing task IDs: {df['task_id'].isna().sum()}")
    print(
        "Missing assignees:",
        df["assignee_employee_id"].isna().sum()
    )

    print("\nFinal check completed.")

if __name__ == "__main__":
    main()
