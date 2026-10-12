
import pandas as pd

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
file_path = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"

df = pd.read_excel(file_path, sheet_name="fact_task")
# Convert dates
for col in ["created_date", "started_date", "due_date", "completed_date"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Validation rules
checks = {
    "duplicate_task_ids": df["task_id"].duplicated().sum(),
    "missing_task_ids": df["task_id"].isna().sum(),
    "missing_assignees": df["assignee_employee_id"].isna().sum(),
    "created_after_due": (
        df["created_date"] > df["due_date"]
    ).sum(),
    "completed_before_started": (
        (df["completed_date"] < df["started_date"])
        & df["completed_date"].notna()
        & df["started_date"].notna()
    ).sum(),
}

print("TASK DATA QUALITY REPORT")
print("=" * 40)

for check, count in checks.items():
    print(f"{check}: {count}")

# Save the records requiring investigation
invalid = df[
    (df["completed_date"] < df["started_date"])
    & df["completed_date"].notna()
    & df["started_date"].notna()
]

output_file = "rejected/task_date_issues.csv"
invalid.to_csv(output_file, index=False)

print(f"\nRecords flagged: {len(invalid)}")
print(f"Review file: {output_file}")
print("\nValidation completed.")
