
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = [
    "clean_data.py",
    "validate_tasks.py",
    "check_mapping.py",
    "data_quality_report.py",
]

def main():
    print("=" * 50)
    print("PULSEIQ ETL PIPELINE")
    print("=" * 50)

    for script in SCRIPTS:
        script_path = PROJECT_ROOT / "src" / script

        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            sys.exit(1)

        print(f"\nRunning {script}...")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
        )

        if result.returncode != 0:
            print(f"FAILED: {script}")
            sys.exit(result.returncode)

        print(f"SUCCESS: {script}")

    print("\nETL pipeline completed successfully!")

if __name__ == "__main__":
    main()
