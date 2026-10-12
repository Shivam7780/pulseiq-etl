
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

CLEAN_FILE = ROOT / "data" / "clean" / "pulseiq_cleaned.xlsx"
LOG_FILE = ROOT / "logs" / "cleaning_log.txt"
REPORT_FILE = ROOT / "reports" / "data_quality_report.xlsx"
OUTPUT_FILE = ROOT / "reports" / "pipeline_summary.txt"


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "PULSEIQ ETL PIPELINE SUMMARY",
        "=" * 40,
    ]

    if CLEAN_FILE.exists():
        workbook = pd.ExcelFile(CLEAN_FILE)
        total_rows = 0

        lines.append("\nCLEANED DATASET")
        for sheet in workbook.sheet_names:
            df = pd.read_excel(workbook, sheet_name=sheet)
            total_rows += len(df)
            lines.append(
                f"{sheet}: {len(df)} rows, {len(df.columns)} columns"
            )

        lines.append(f"\nTotal rows across sheets: {total_rows}")
    else:
        lines.append("\nCleaned dataset: MISSING")

    lines.append(
        f"\nCleaning log: {'Available' if LOG_FILE.exists() else 'Missing'}"
    )
    lines.append(
        f"Quality report: {'Available' if REPORT_FILE.exists() else 'Missing'}"
    )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nSummary saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
