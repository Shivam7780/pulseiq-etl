# PulseIQ ETL & People Analytics

A starter repository for Phase 1 (data foundations and dashboards) and Phase 2 (attendance, attrition, team productivity, payroll, and budget analytics).

## Stack
- Python 3.11+
- PostgreSQL
- SQLAlchemy + psycopg
- Streamlit
- Plotly
- Pandas

## Quick start

1. Copy these files into your existing `pulseiq-etl` repository. **Do not overwrite your existing Phase 1 files without checking them first.**
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.streamlit/secrets.toml` (never commit this file):
   ```toml
   [database]
   url = "postgresql+psycopg://USER:PASSWORD@localhost:5432/pulseiq_warehouse"
   ```
   Or set `DATABASE_URL` as an environment variable.
5. Create the reporting views described in `database/metric_views/README.md` against your actual warehouse schema.
6. Run:
   ```bash
   streamlit run dashboards/app.py
   ```

## Reporting-view contract

The dashboard reads from views in the `analytics` schema. The expected view names and columns are documented in `database/metric_views/README.md`. The source warehouse schema in your existing project may use different names; map your real columns in SQL views rather than changing the dashboard's business definitions.

The app intentionally shows a helpful warning when a view is missing. It does not invent data.

## Privacy and safety
- Do not commit raw employee-level data, salary details, credentials, or the validation answer key.
- Attrition risk is shown only in grouped form and is labelled **Predicted, not certain**.
- Groups below the configured minimum size are suppressed.
- Keep `.streamlit/secrets.toml`, `.env`, raw data and private evidence out of public GitHub.

## Suggested repository layout

```text
pulseiq-etl/
├── dashboards/
│   ├── app.py
│   ├── common.py
│   └── pages/
├── database/metric_views/
├── etl/
├── validation/
├── docs/
└── reports/
```

## Phase 2 completion
Do not mark a task complete until its metric definitions, source mapping, checks, screenshot, and three numeric findings are recorded in `reports/phase-2-review.md`.
