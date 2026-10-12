
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT / "data" / "raw" / (
    "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)
CLEAN_DIR = ROOT / "data" / "clean"
LOG_DIR = ROOT / "logs"


def clean_dataframe(df):
    df = df.copy()

    # Standardize column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    # Remove entirely empty rows and columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Trim extra spaces from text values
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    return df


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_FILE}")

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logs = []
    cleaned_sheets = {}

    with pd.ExcelFile(RAW_FILE) as workbook:
        for sheet in workbook.sheet_names:
            original = pd.read_excel(workbook, sheet_name=sheet)
            cleaned = clean_dataframe(original)

            cleaned_sheets[sheet] = cleaned

            message = (
                f"{sheet}: input_rows={len(original)}, "
                f"output_rows={len(cleaned)}, "
                f"removed_rows={len(original) - len(cleaned)}, "
                f"missing_values={int(cleaned.isna().sum().sum())}"
            )

            logs.append(message)
            print(message)

    output_file = CLEAN_DIR / "pulseiq_cleaned.xlsx"

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet, df in cleaned_sheets.items():
            df.to_excel(
                writer,
                sheet_name=sheet[:31],
                index=False
            )

    log_file = LOG_DIR / "cleaning_log.txt"
    log_file.write_text("\n".join(logs), encoding="utf-8")

    print("\nETL cleaning completed successfully!")
    print(f"Cleaned workbook: {output_file}")
    print(f"Cleaning log: {log_file}")


if __name__ == "__main__":
    main()
