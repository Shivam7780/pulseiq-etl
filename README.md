# PulseIQ ETL Analytics

## Project Overview
PulseIQ ETL Analytics is a Python-based data pipeline for cleaning, validating, and analyzing workforce data. It includes a PostgreSQL analytics warehouse, dimensional modeling, repeatable fact-table loads, and SQL-based reporting.

## Technologies Used
- Python
- Pandas and OpenPyXL
- SQLAlchemy and psycopg2
- PostgreSQL
- Python-dotenv
- Pandera and PyArrow

## Main Features
- Cleans and standardizes workforce data.
- Validates employee, payroll, attendance, leave, and task records.
- Produces data-quality reports and rejected-record files.
- Implements a dimensional warehouse with date, employee, department, role, and leave-type dimensions.
- Loads payroll, attendance, and monthly headcount facts using repeatable upserts.
- Runs SQL analytics for monthly payroll, headcount, and attendance by department.
- Reconciles query results against source data and documents unmatched records.

## Project Structure
- `data/raw/` — Source datasets.
- `data/clean/` — Cleaned source workbook.
- `src/` — Cleaning, validation, and ETL scripts.
- `sql/schema.sql` — Warehouse schema definition.
- `sql/queries/` — Analytics SQL queries.
- `docs/` — Star schema design and diagram documentation.
- `reports/` — Query results, reconciliation, and data-quality reports.
- `logs/` — Pipeline logs.
- `rejected/` — Records flagged for review.
- `requirements.txt` — Python dependencies.
- `.env` — Local database connection configuration; do not commit this file.

## Setup
1. Install and start Docker Desktop.
2. Start the PostgreSQL container if it is not already running.
3. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Configure `DATABASE_URL` in the local `.env` file. Use your own valid database credentials. Do not put passwords in source files or commit `.env`.

## Running the Original Cleaning Pipeline
From the project root:

```powershell
python .\src\run_pipeline.py
```

## Warehouse and Analytics
The warehouse schema is `warehouse_v2`. The database connection is read from the local `.env` file by loaders that use `DATABASE_URL`.

Analytics queries:
- `sql/queries/01_monthly_payroll_by_department.sql`
- `sql/queries/02_monthly_headcount_by_department.sql`
- `sql/queries/03_monthly_attendance_by_department.sql`

Run a query in PowerShell by piping its contents to `psql`. For example:

```powershell
Get-Content sql/queries/01_monthly_payroll_by_department.sql -Raw |
    docker exec -i pulseiq-postgres psql -U pulseiq_user -d pulseiq_warehouse -v ON_ERROR_STOP=1
```

Use the correct database for your environment. Test loaders should target the test database, not the production or primary warehouse.

## Task 2 Reconciliation Results
The recorded reconciliation report shows:

| Query | Source groups | Report groups | Matching groups | Metric mismatches after exclusions | Status |
|---|---:|---:|---:|---:|---|
| Monthly payroll by department | 198 | 198 | 198 | 0 | PASS |
| Monthly headcount by department | 891 | 891 | 891 | 0 | PASS |
| Monthly attendance by department | 198 | 198 | 198 | 0 | PASS |

See `reports/query_reconciliation_summary.csv` for the detailed reconciliation record.

## Data Quality Notes
- Payroll ETL processed 7,260 records from 7,344 source rows; 84 records were unmatched.
- Attendance ETL processed 7,258 records from 7,343 source rows; 85 records were unmatched.
- Unmatched records are documented in the reports and should be investigated before any attempt to load them.
- Do not silently discard or alter source data to make reconciliation pass.
- The headcount loader processed 891 records and remained at 891 rows after a second run.
- Payroll remained at 7,260 rows after a second test load.
- Attendance remained at 7,258 rows after a second test load.
- These repeatability checks were performed against the test database.

## Project Status
The three recorded analytics reconciliation checks passed. Repeatability checks passed for the headcount, payroll, and attendance test loads. Unmatched payroll and attendance records remain documented data-quality exceptions and require review.
