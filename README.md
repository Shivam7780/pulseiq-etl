\# PulseIQ Analytics — ETL Pipeline



\## 1. Project Overview



This project builds an ETL (Extract, Transform, Load) pipeline for the PulseIQ Analytics star-schema dataset. It processes Excel data, standardizes fields, removes exact duplicate records, and performs data quality checks.



\## 2. Technologies Used



\- Python

\- Pandas

\- OpenPyXL

\- Excel

\- PowerShell



\## 3. Project Structure



```text

pulseiq-etl/

├── data/

│   ├── raw/

│   └── clean/

├── src/

│   ├── clean\_data.py

│   ├── inspect\_dataset.py

│   ├── validate\_data.py

│   ├── validate\_tasks.py

│   ├── check\_mapping.py

│   ├── data\_quality\_report.py

│   ├── final\_check.py

│   ├── pipeline\_summary.py

│   └── run\_pipeline.py

├── logs/

├── rejected/

└── reports/

```



\## 4. Pipeline Workflow



1\. Extract data from the raw Excel workbook.

2\. Standardize column names and trim text fields.

3\. Remove exact duplicate rows and empty rows or columns according to the cleaning rules.

4\. Validate task IDs, required values, dates, and employee mappings.

5\. Record records requiring investigation.

6\. Generate data quality and pipeline summary reports.



\## 5. How to Run



From the project root, activate the Python environment if required and run:



```powershell

python .\\src\\run\_pipeline.py

```



Run individual scripts when investigating issues:



```powershell

python .\\src\\clean\_data.py

python .\\src\\validate\_tasks.py

python .\\src\\data\_quality\_report.py

python .\\src\\final\_check.py

python .\\src\\pipeline\_summary.py

```



\## 6. Current Validation Findings



The task validation run reported:



\- Task records: 28,868

\- Duplicate task IDs: 0

\- Missing task IDs: 0

\- Unmatched task assignments: 0

\- Completion dates earlier than start dates: 12 records requiring investigation



These results describe the observed task validation run, not a guarantee that every sheet passes all data quality rules.



\## 7. Output Files



\- `data/clean/pulseiq\_cleaned.xlsx` — cleaned workbook

\- `logs/cleaning\_log.txt` — cleaning log

\- `reports/data\_quality\_report.xlsx` — data quality summary and issue details

\- `reports/pipeline\_summary.txt` — workbook row and column summary

\- `rejected/task\_date\_issues.csv` — task date records requiring review, if generated at this path



\## 8. Data Quality Notes



Missing values should be handled according to business rules. For example, an employee's exit date may legitimately be blank. Date inconsistencies should be investigated against the source data rather than silently corrected or deleted.



\## 9. Project Status



The initial cleaning, task validation, employee mapping, and reporting scripts have been executed. Final completion requires confirming that all output paths are consistent, validation counts are generated dynamically, and the complete pipeline runs successfully from start to finish.

