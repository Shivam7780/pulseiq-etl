# Phase 1 Review — Attendance & Leave Trends

## 1. Objective
Analyze workforce attendance and leave trends, identify late-arrival patterns, calculate rolling averages, and highlight AI-flagged months.

## 2. Work Completed
- Loaded attendance and leave data into the data warehouse.
- Calculated monthly and department-level attendance rates.
- Calculated late-arrival rates and three-month rolling averages.
- Summarized leave days by leave type and status.
- Filtered AI anomaly records for `attendance_monthly_features`.
- Generated six charts in `reports/charts/`.
- Created `reports/insightsattendance.md`.
- Packaged the six charts and insight note into `reports/attendance_leave_dashboard_export.zip`.

## 3. Key Findings
1. **Attendance target:** The attendance benchmark is 94%. Department and monthly results should be compared against this target to identify periods requiring review.
2. **AI flags:** There are 221 flagged records across 18 months, from April 2025 to September 2026. July 2026 has the highest monthly count, with 22 flagged records.
3. **Leave data quality:** The medical-leave category contains seven approved requests totalling 910 leave days. This unusual total requires source-data validation before drawing conclusions.

## 4. Charts and Outputs
- `reports/charts/01_monthly_attendance_rate.png`
- `reports/charts/02_department_attendance.png`
- `reports/charts/03_attendance_rolling_average.png`
- `reports/charts/04_late_arrival_trend.png`
- `reports/charts/05_leave_days_by_type.png`
- `reports/charts/06_ai_flags_by_month.png`
- `reports/attendance_monthly_analysis.csv`
- `reports/attendance_ai_flags_by_month.csv`
- `reports/attendance_leave_summary.csv`
- `reports/insightsattendance.md`
- `reports/attendance_leave_dashboard_export.zip`

## 5. Limitations
- The available attendance fact table is monthly; weekday-level attendance rates cannot be reliably calculated without daily attendance data.
- Small department-month groups can produce unstable percentages.
- AI flags indicate potential anomalies and do not establish misconduct.
- The unusual medical-leave total needs validation.
- The original Section 10 review template was not found in the project files.

## 6. Pending Items
- Import the charts into the required dashboard platform and export the actual dashboard if a live dashboard is required.
- Compare this review against the original Section 10 template when it becomes available.
- Validate unusual leave totals and review flagged periods before making operational decisions.

## 7. Status
Attendance and leave analysis, charts, insight note, and chart-package ZIP are complete. A live dashboard export and template-specific review remain pending.
