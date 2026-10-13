
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEAN_FILE = (
    PROJECT_ROOT
    / "clean"
    / "pulseiq_cleaned.xlsx"
)


def inspect_cleaned_dataset():
    if not CLEAN_FILE.exists():
        print(f"ERROR: Cleaned file not found: {CLEAN_FILE}")
        return

    print("Cleaned dataset found successfully!")
    print(f"File: {CLEAN_FILE}")

    excel_file = pd.ExcelFile(CLEAN_FILE)

    print("\nSheets available in cleaned dataset:")
    print(excel_file.sheet_names)

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(
            CLEAN_FILE,
            sheet_name=sheet_name
        )

        print(f"\n{'=' * 60}")
        print(f"Sheet: {sheet_name}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"Duplicate rows: {df.duplicated().sum()}")
        print(f"Missing values: {df.isna().sum().sum()}")

        missing = df.isna().sum()
        missing = missing[missing > 0]

        if not missing.empty:
            print("\nColumns with missing values:")
            print(missing.to_string())
        else:
            print("No missing values found.")

    print("\nCleaned dataset inspection completed.")


if __name__ == "__main__":
    inspect_cleaned_dataset()
