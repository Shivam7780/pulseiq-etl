
import pandas as pd

file_path = "clean/pulseiq_cleaned.xlsx"

tasks = pd.read_excel(file_path, sheet_name="fact_task")
employees = pd.read_excel(file_path, sheet_name="dim_employee")

# Standardize IDs before merging
tasks["assignee_employee_id"] = (
    tasks["assignee_employee_id"]
    .astype("string")
    .str.strip()
    .str.upper()
)

employees["employee_id"] = (
    employees["employee_id"]
    .astype("string")
    .str.strip()
    .str.upper()
)

# Check whether task assignees exist in the employee table
employee_ids = set(employees["employee_id"].dropna())

tasks["employee_match"] = tasks["assignee_employee_id"].isin(
    employee_ids
)

print("Total tasks:", len(tasks))
print("Matched tasks:", int(tasks["employee_match"].sum()))
print("Unmatched tasks:", int((~tasks["employee_match"]).sum()))

print("\nUnmatched assignee IDs:")
print(
    tasks.loc[~tasks["employee_match"], "assignee_employee_id"]
    .dropna()
    .drop_duplicates()
    .to_list()
)
