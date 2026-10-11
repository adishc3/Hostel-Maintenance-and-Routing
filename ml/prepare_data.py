import argparse
import os
from pathlib import Path
import pandas as pd


PRIORITY_MAP = {
    "urgent": "High",
    "routine": "Medium",
    "cosmetic": "Low",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


def standardize_priority(value: str) -> str:
    if not isinstance(value, str):
        return "Medium"
    v = value.strip().lower()
    return PRIORITY_MAP.get(v, "Medium")


def prepare_dataset(input_csv: Path, output_csv: Path) -> None:
    df = pd.read_csv(input_csv)

    print("Columns:", list(df.columns))
    print("Total rows:", len(df))

    # Basic cleaning
    df = df.drop_duplicates()

    # Drop empty or null complaints
    if "complaint" in df.columns:
        df["complaint"] = df["complaint"].astype(str)
        df = df[df["complaint"].str.strip() != ""]

    # Standardize priority
    if "priority" in df.columns:
        df["priority_original"] = df["priority"]
        df["priority"] = df["priority"].apply(standardize_priority)
    else:
        df["priority"] = "Medium"

    # Report class distribution
    print("\nPriority value counts (standardized):")
    print(df["priority"].value_counts(dropna=False))

    if "category" in df.columns:
        print("\nCategory value counts (top 20):")
        print(df["category"].value_counts().head(20))

    # Ensure output dir exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Cleaned dataset written to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Prepare dataset for Smart Hostel ML")
    parser.add_argument("--input", type=Path, default=Path("../hotel_maintenance_dataset.csv"))
    parser.add_argument("--output", type=Path, default=Path("dataset/cleaned_hotel_maintenance_dataset.csv"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_csv = (root / args.input).resolve()
    output_csv = (root / "ml" / args.output).resolve()

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    prepare_dataset(input_csv, output_csv)


if __name__ == "__main__":
    main()
