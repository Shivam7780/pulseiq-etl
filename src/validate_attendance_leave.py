
import pandas as pd
from pathlib import Path

FILE_PATH = Path("data/clean/pulseiq_cleaned.xlsx")
REJECTED_DIR = Path("rejected")


def validate_attendance_leave():
    attendance = pd.read_excel(
        FILE_PATH, sheet_name="fact_attendance_monthly"
    )
    leave = pd.read_excel(
        FILE_PATH, sheet_name="fact_leave"
    )

    # Attendance validation
    attendance_required = {
        "employee_id", "scheduled_days", "present_days"
    }
    missing = attendance_required - set(attendance.columns)

    if missing:
        raise ValueError(
            f"Attendance columns missing: {sorted(missing)}"
        )

    for column in ["scheduled_days", "present_days"]:
        attendance[column] = pd.to_numeric(
            attendance[column], errors="raise"
        )

        if (attendance[column].dropna() < 0).any():
            raise ValueError(
                f"Attendance validation failed: negative {column}"
            )

    invalid_attendance = (
        attendance["present_days"].notna()
        & attendance["scheduled_days"].notna()
        & (
            attendance["present_days"]
            > attendance["scheduled_days"]
        )
    )

    if invalid_attendance.any():
        raise ValueError(
            "Attendance validation failed: "
            f"{int(invalid_attendance.sum())} rows have "
            "present_days greater than scheduled_days"
        )

    if attendance["employee_id"].isna().any():
        raise ValueError(
            "Attendance validation failed: missing employee IDs"
        )

    # Leave validation
    leave_required = {
        "employee_id", "start_date", "end_date", "days"
    }
    missing = leave_required - set(leave.columns)

    if missing:
        raise ValueError(
            f"Leave columns missing: {sorted(missing)}"
        )

    leave["days"] = pd.to_numeric(
        leave["days"], errors="raise"
    )

    if (leave["days"].dropna() < 0).any():
        raise ValueError(
            "Leave validation failed: negative leave days"
        )

    start = pd.to_datetime(
        leave["start_date"], errors="coerce"
    )
    end = pd.to_datetime(
        leave["end_date"], errors="coerce"
    )

    invalid_dates = (
        (leave["start_date"].notna() & start.isna())
        | (leave["end_date"].notna() & end.isna())
        | (
            start.notna()
            & end.notna()
            & (end < start)
        )
    )

    # Save invalid leave records for review
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    rejected_file = REJECTED_DIR / "leave_date_issues.csv"

    if invalid_dates.any():
        rejected_records = leave.loc[invalid_dates].copy()
        rejected_records.to_csv(rejected_file, index=False)

        print("\nINVALID OR REVERSED LEAVE DATE RECORDS:")
        columns_to_show = [
            col for col in [
                "leave_request_id",
                "employee_id",
                "start_date",
                "end_date",
                "days"
            ]
            if col in leave.columns
        ]

        print(
            rejected_records[columns_to_show].to_string(
                index=False
            )
        )
        print(
            f"Total problematic leave records: "
            f"{int(invalid_dates.sum())}"
        )
        print(f"Rejected records saved to: {rejected_file}")

    else:
        # Remove an old rejection file if no issues remain
        if rejected_file.exists():
            rejected_file.unlink()

        print("Leave date validation passed.")

    if leave["employee_id"].isna().any():
        raise ValueError(
            "Leave validation failed: missing employee IDs"
        )

    # Final status
    if invalid_dates.any():
        print(
            "\nATTENDANCE VALIDATION PASSED; "
            "LEAVE VALIDATION NEEDS REVIEW"
        )
    else:
        print("ATTENDANCE AND LEAVE VALIDATION PASSED")

    print(f"Attendance rows checked: {len(attendance)}")
    print(f"Leave rows checked: {len(leave)}")


if __name__ == "__main__":
    validate_attendance_leave()
