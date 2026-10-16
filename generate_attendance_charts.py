import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

reports = Path("reports")
charts = reports / "charts"
charts.mkdir(parents=True, exist_ok=True)

monthly = pd.read_csv(reports / "attendance_monthly_analysis.csv")
flags = pd.read_csv(reports / "attendance_ai_flags_by_month.csv")
leave = pd.read_csv(reports / "attendance_leave_summary.csv")

monthly["month"] = monthly["month"].astype(str)
flags["month"] = flags["month"].astype(str)

# 1. Overall monthly attendance and target
overall = monthly.groupby("month", as_index=False).agg(
    scheduled_days=("scheduled_days", "sum"),
    present_days=("present_days", "sum"),
    half_days_unpaid=("half_days_unpaid", "sum"),
    flagged_records=("flagged_records", "max")
)
overall["attendance_rate_pct"] = (
    100 * (overall["present_days"] + 0.5 * overall["half_days_unpaid"])
    / overall["scheduled_days"].replace(0, float("nan"))
)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(overall["month"], overall["attendance_rate_pct"], marker="o", label="Attendance rate")
ax.axhline(94, linestyle="--", label="94% target")
for _, r in overall[overall["flagged_records"] > 0].iterrows():
    ax.annotate("AI flag", (r["month"], r["attendance_rate_pct"]),
                xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7)
ax.set_title("Monthly Attendance Rate — AI flags marked")
ax.set_ylabel("Attendance rate (%)")
ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=60)
ax.legend()
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "01_monthly_attendance_rate.png", dpi=160)
plt.close(fig)

# 2. Department attendance trends
fig, ax = plt.subplots(figsize=(13, 6))
for dept, group in monthly.groupby("department_id"):
    group = group.sort_values("month")
    ax.plot(group["month"], group["attendance_rate_pct"], marker=".", linewidth=1, label=dept)
ax.axhline(94, linestyle="--", label="94% target")
ax.set_title("Monthly Attendance Rate by Department")
ax.set_ylabel("Attendance rate (%)")
ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=60)
ax.legend(ncol=4, fontsize=8)
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "02_department_attendance.png", dpi=160)
plt.close(fig)

# 3. Department three-month rolling attendance average
fig, ax = plt.subplots(figsize=(13, 6))
for dept, group in monthly.groupby("department_id"):
    group = group.sort_values("month")
    ax.plot(group["month"], group["attendance_3m_avg_pct"], marker=".", linewidth=1, label=dept)
ax.axhline(94, linestyle="--", label="94% target")
ax.set_title("Three-Month Rolling Attendance Average by Department")
ax.set_ylabel("Rolling attendance rate (%)")
ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=60)
ax.legend(ncol=4, fontsize=8)
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "03_attendance_rolling_average.png", dpi=160)
plt.close(fig)

# 4. Overall late-arrival trend and rolling averages
late = monthly.groupby("month", as_index=False).agg(
    late_arrivals=("late_arrivals", "sum"),
    present_days=("present_days", "sum")
)
late["late_arrival_rate_pct"] = (
    100 * late["late_arrivals"] / late["present_days"].replace(0, float("nan"))
)
late = late.sort_values("month")
late["late_arrival_3m_avg_pct"] = late["late_arrival_rate_pct"].rolling(3, min_periods=1).mean()
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(late["month"], late["late_arrival_rate_pct"], marker="o", label="Late-arrival rate")
ax.plot(late["month"], late["late_arrival_3m_avg_pct"], linestyle="--", label="3-month rolling average")
for _, r in flags.iterrows():
    ax.annotate("AI flag", (r["month"], late.loc[late["month"] == r["month"], "late_arrival_rate_pct"].iloc[0]),
                xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7)
ax.set_title("Monthly Late-Arrival Rate — AI flags marked")
ax.set_ylabel("Late arrivals / present days (%)")
ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=60)
ax.legend()
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "04_late_arrival_trend.png", dpi=160)
plt.close(fig)

# 5. Leave days by type and status
leave["leave_days"] = pd.to_numeric(leave["leave_days"], errors="coerce").fillna(0)
pivot = leave.pivot_table(index="leave_type_code", columns="status",
                          values="leave_days", aggfunc="sum", fill_value=0)
fig, ax = plt.subplots(figsize=(11, 5))
pivot.plot(kind="bar", ax=ax)
ax.set_title("Leave Days by Type and Status")
ax.set_ylabel("Leave days")
ax.set_xlabel("Leave type")
ax.tick_params(axis="x", rotation=0)
ax.legend(title="Status")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "05_leave_days_by_type.png", dpi=160)
plt.close(fig)

# 6. AI-flagged records by month
flags = flags.sort_values("month")
fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(flags["month"], flags["flagged_records"])
ax.bar_label(bars, fontsize=8)
ax.set_title("AI-Flagged Attendance Records by Month")
ax.set_ylabel("Flagged records")
ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=60)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(charts / "06_ai_flags_by_month.png", dpi=160)
plt.close(fig)

print("Charts created in:", charts.resolve())
for f in sorted(charts.glob("*.png")):
    print(f.name, f.stat().st_size, "bytes")
print("Note: weekday-level attendance chart omitted because the source is monthly.")
