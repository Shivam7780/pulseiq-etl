
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "clean" / "pulseiq_cleaned.xlsx"


def investigate_tasks():
    summary = pd.read_excel(
        FILE, sheet_name="reference_summary_dept_month"
    )
    tasks = pd.read_excel(FILE, sheet_name="fact_task")

    print("TASK TABLE COLUMNS:")
    print(tasks.columns.tolist())

    print("\nTASK STATUS COUNTS:")
    if "status" in tasks.columns:
        print(tasks["status"].value_counts(dropna=False))

    missing = summary[summary["tasks"].isna()]

    print("\nMISSING DEPARTMENT-MONTH COMBINATIONS:")
    for _, row in missing.iterrows():
        dept = row["department_id"]
        month = pd.to_datetime(row["month"])

        print(f"\nDepartment: {dept}, Month: {month:%Y-%m}")

        if "department_id" not in tasks.columns:
            print("Cannot match: department_id missing in task table")
            continue

        department_tasks = tasks[
            tasks["department_id"].astype(str).str.strip()
            == str(dept).strip()
        ]

        print("Department task records:", len(department_tasks))

        if "created_date" in tasks.columns:
            dates = pd.to_datetime(
                department_tasks["created_date"], errors="coerce"
            )
            month_tasks = department_tasks[
                dates.dt.to_period("M") == month.to_period("M")
            ]
            print("Tasks created in month:", len(month_tasks))

            if "status" in month_tasks.columns:
                print("Status breakdown:")
                print(
                    month_tasks["status"]
                    .value_counts(dropna=False)
                    .to_dict()
                )


if __name__ == "__main__":
    investigate_tasks()
