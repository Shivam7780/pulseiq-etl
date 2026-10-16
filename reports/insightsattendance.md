# Task 4 — Attendance Trends Analysis

## Scope and method
Analysis uses `fact_attendance_monthly`, `fact_leave`, and flagged records in `fact_anomaly` where `source_dataset = attendance_monthly_features`. Attendance rate is calculated as (present days + 0.5 × unpaid half-days) / scheduled days. Late-arrival rate is late arrivals / present days. Three-month rolling averages are calculated separately by department. The attendance target is 94%.

## Three findings
1. Across the 18 observed months, the unweighted mean of monthly overall attendance rates was 94.18% (descriptive average, not employee-weighted). The lowest month was 2026-05 at 92.89%.
2. The AI source contains 221 flagged attendance records across 18 months. The highest monthly count was 22 in 2026-07.
3. The mean of monthly late-arrival rates was 6.83%. Review departments and months with elevated late-arrival rates alongside their three-month rolling averages.

## AI flags
AI-flagged records are marked `AI flag` in `attendance_monthly_analysis.csv`. Monthly counts and reason codes are available in `attendance_ai_flags_by_month.csv`. These flags indicate model-detected anomalies and should be investigated, not treated as proof of misconduct or error.

## Leave analysis
Leave requests and days are summarized by leave type and status in `attendance_leave_summary.csv`. Validate unusually large totals or small request counts before drawing policy conclusions.

## Limitation
The available attendance fact is monthly, not daily. Therefore weekday-level attendance rates cannot be calculated reliably from this source. Leave start dates can describe the weekdays on which leave begins, but they are not a substitute for daily attendance. Small department-month denominators can also create extreme rates; interpret them with group size in mind.
