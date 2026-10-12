
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
REPORT_DIR = ROOT / "reports"
ISSUES_FILE = ROOT / "rejected" / "task_date_issues.csv"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Read the cleaned task data
df = pd.read_excel(CLEAN_FILE, sheet_name="fact_task")

# Calculate actual validation results
checks = [
    ("Duplicate task IDs", int(df["task_id"].duplicated().sum())),
    ("Missing task IDs", int(df["task_id"].isna().sum())),
    ("Missing assignees", int(df["assignee_employee_id"].isna().sum())),
    (
        "Created date after due date",
        int((
            pd.to_datetime(df["created_date"], errors="coerce")
            > pd.to_datetime(df["due_date"], errors="coerce")
        ).sum()),
    ),
    (
        "Completed date before start date",
        int((
            (pd.to_datetime(df["completed_date"], errors="coerce")
             < pd.to_datetime(df["started_date"], errors="coerce"))
            & pd.to_datetime(df["completed_date"], errors="coerce").notna()
            & pd.to_datetime(df["started_date"], errors="coerce").notna()
        ).sum()),
    ),
]

rows = []
for check, count in checks:
    rows.append({
        "check": check,
        "count": count,
        "status": "PASS" if count == 0 else "REVIEW REQUIRED",
    })

summary = pd.DataFrame(rows)

# Include the detailed date-issue records when available
if ISSUES_FILE.exists():
    issues = pd.read_csv(ISSUES_FILE)
else:
    issues = pd.DataFrame(
        columns=["task_id", "status", "started_date", "completed_date"]
    )

output_file = REPORT_DIR / "data_quality_report.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    summary.to_excel(writer, sheet_name="Summary", index=False)
    issues.to_excel(writer, sheet_name="Date Issues", index=False)

print("DATA QUALITY REPORT")
print("=" * 45)
print(summary.to_string(index=False))
print(f"\nReport saved to: {output_file}")
