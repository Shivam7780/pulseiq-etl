import pandas as pd
from pathlib import Path

root = Path(".")
source = root / "data" / "clean" / "pulseiq_cleaned.xlsx"
out = root / "reports"
out.mkdir(exist_ok=True)

attendance = pd.read_excel(source, sheet_name="fact_attendance_monthly")
anomaly = pd.read_excel(source, sheet_name="fact_anomaly")
leave = pd.read_excel(source, sheet_name="fact_leave")

attendance["period_end_date"] = pd.to_datetime(attendance["period_end_date"])
attendance["month"] = attendance["period_end_date"].dt.to_period("M").astype(str)

monthly = attendance.groupby(["month", "department_id"], as_index=False).agg(
    scheduled_days=("scheduled_days", "sum"),
    present_days=("present_days", "sum"),
    half_days_unpaid=("half_days_unpaid", "sum"),
    late_arrivals=("late_arrivals", "sum"),
    paid_leave_days=("paid_leave_days", "sum"),
    unpaid_absence_days=("unpaid_absence_days", "sum"),
    employee_records=("employee_id", "nunique")
)

monthly["attendance_rate_pct"] = (
    100 * (monthly["present_days"] + 0.5 * monthly["half_days_unpaid"])
    / monthly["scheduled_days"].replace(0, pd.NA)
)
monthly["late_arrival_rate_pct"] = (
    100 * monthly["late_arrivals"]
    / monthly["present_days"].replace(0, pd.NA)
)
monthly = monthly.sort_values(["department_id", "month"])
monthly["attendance_3m_avg_pct"] = monthly.groupby("department_id")["attendance_rate_pct"].transform(
    lambda s: s.rolling(3, min_periods=1).mean()
)
monthly["late_arrival_3m_avg_pct"] = monthly.groupby("department_id")["late_arrival_rate_pct"].transform(
    lambda s: s.rolling(3, min_periods=1).mean()
)

flags = anomaly[
    (anomaly["source_dataset"].astype(str) == "attendance_monthly_features")
    & (anomaly["flagged"].astype(str).str.upper() == "Y")
].copy()
flags["period"] = pd.to_datetime(flags["period"], errors="coerce")
flags["month"] = flags["period"].dt.to_period("M").astype(str)

flag_month = flags.groupby("month", as_index=False).agg(
    flagged_records=("result_id", "count"),
    flagged_employees=("employee_id", "nunique"),
    reasons=("reason_code", lambda s: ", ".join(sorted(s.dropna().astype(str).unique())))
)
flag_month["ai_flag"] = "AI flag"

monthly = monthly.merge(flag_month, on="month", how="left")
monthly["flagged_records"] = monthly["flagged_records"].fillna(0).astype(int)
monthly["flagged_employees"] = monthly["flagged_employees"].fillna(0).astype(int)
monthly["ai_flag"] = monthly["ai_flag"].fillna("")
monthly["attendance_target_pct"] = 94.0

monthly.sort_values(["month", "department_id"]).to_csv(out / "attendance_monthly_analysis.csv", index=False)
flag_month.to_csv(out / "attendance_ai_flags_by_month.csv", index=False)

leave_summary = leave.groupby(["leave_type_code", "status"], dropna=False, as_index=False).agg(
    leave_requests=("leave_request_id", "count"),
    leave_days=("days", "sum")
)
leave_summary.to_csv(out / "attendance_leave_summary.csv", index=False)

month_overall = attendance.groupby("month", as_index=False).agg(
    scheduled_days=("scheduled_days", "sum"),
    present_days=("present_days", "sum"),
    half_days_unpaid=("half_days_unpaid", "sum"),
    late_arrivals=("late_arrivals", "sum")
)
month_overall["attendance_rate_pct"] = 100 * (
    month_overall["present_days"] + 0.5 * month_overall["half_days_unpaid"]
) / month_overall["scheduled_days"].replace(0, pd.NA)
month_overall["late_arrival_rate_pct"] = 100 * (
    month_overall["late_arrivals"] / month_overall["present_days"].replace(0, pd.NA)
)
month_overall = month_overall.merge(flag_month[["month", "flagged_records"]], on="month", how="left")
month_overall["flagged_records"] = month_overall["flagged_records"].fillna(0).astype(int)

lowest = month_overall.dropna(subset=["attendance_rate_pct"]).nsmallest(1, "attendance_rate_pct")
highest_flags = flag_month.sort_values("flagged_records", ascending=False).head(1)
total_flags = len(flags)
months_flagged = flags["month"].nunique()
avg_attendance = month_overall["attendance_rate_pct"].mean()
avg_late = month_overall["late_arrival_rate_pct"].mean()

finding1 = (
    f"Across the {len(month_overall)} observed months, the unweighted mean of monthly overall "
    f"attendance rates was {avg_attendance:.2f}% (descriptive average, not employee-weighted). "
    f"The lowest month was {lowest.iloc[0]['month']} at {lowest.iloc[0]['attendance_rate_pct']:.2f}%."
    if not lowest.empty else "Attendance-rate data was insufficient to calculate a monthly comparison."
)
finding2 = (
    f"The AI source contains {total_flags} flagged attendance records across {months_flagged} months. "
    f"The highest monthly count was {int(highest_flags.iloc[0]['flagged_records'])} in "
    f"{highest_flags.iloc[0]['month']}."
    if not highest_flags.empty else "No flagged attendance records were found for the requested source dataset."
)
finding3 = (
    f"The mean of monthly late-arrival rates was {avg_late:.2f}%. "
    "Review departments and months with elevated late-arrival rates alongside their three-month rolling averages."
    if pd.notna(avg_late) else "Late-arrival rates could not be calculated from the available data."
)

note = f"""# Task 4 — Attendance Trends Analysis

## Scope and method
Analysis uses `fact_attendance_monthly`, `fact_leave`, and flagged records in `fact_anomaly` where `source_dataset = attendance_monthly_features`. Attendance rate is calculated as (present days + 0.5 × unpaid half-days) / scheduled days. Late-arrival rate is late arrivals / present days. Three-month rolling averages are calculated separately by department. The attendance target is 94%.

## Three findings
1. {finding1}
2. {finding2}
3. {finding3}

## AI flags
AI-flagged records are marked `AI flag` in `attendance_monthly_analysis.csv`. Monthly counts and reason codes are available in `attendance_ai_flags_by_month.csv`. These flags indicate model-detected anomalies and should be investigated, not treated as proof of misconduct or error.

## Leave analysis
Leave requests and days are summarized by leave type and status in `attendance_leave_summary.csv`. Validate unusually large totals or small request counts before drawing policy conclusions.

## Limitation
The available attendance fact is monthly, not daily. Therefore weekday-level attendance rates cannot be calculated reliably from this source. Leave start dates can describe the weekdays on which leave begins, but they are not a substitute for daily attendance. Small department-month denominators can also create extreme rates; interpret them with group size in mind.
"""
(out / "insightsattendance.md").write_text(note, encoding="utf-8")

print("Created:")
for name in [
    "attendance_monthly_analysis.csv",
    "attendance_ai_flags_by_month.csv",
    "attendance_leave_summary.csv",
    "insightsattendance.md"
]:
    print(out / name)
print("\nAI-flagged records:", total_flags)
print("Flagged months:", months_flagged)
print("Highest flag month:", highest_flags.iloc[0]["month"] if not highest_flags.empty else "None")
