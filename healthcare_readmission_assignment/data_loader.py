"""Load the provided diabetes dataset into PostgreSQL."""

import csv
from pathlib import Path

import repository

DATA_DIR = Path(__file__).parent / "data"

# Assignment-required columns only (from the full UCI CSV)
SELECTED_COLUMNS = (
    "encounter_id",
    "patient_nbr",
    "age",
    "time_in_hospital",
    "number_inpatient",
    "number_emergency",
    "number_outpatient",
    "num_medications",
    "num_lab_procedures",
    "discharge_disposition_id",
    "admission_type_id",
    "readmitted",
)


def _row_to_tuple(row: dict[str, str]) -> tuple:
    """Map one CSV row to a patient_encounters insert tuple."""
    return (
        int(row["encounter_id"]),
        int(row["patient_nbr"]),
        row["age"],
        int(row["time_in_hospital"]),
        int(row["number_inpatient"]),
        int(row["number_emergency"]),
        int(row["number_outpatient"]),
        int(row["num_medications"]),
        int(row["num_lab_procedures"]),
        int(row["discharge_disposition_id"]),
        int(row["admission_type_id"]),
        row["readmitted"],
    )


def read_encounter_rows(csv_path: Path) -> list[tuple]:
    """Read the CSV and return selected-column tuples."""
    rows: list[tuple] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(SELECTED_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for row in reader:
            rows.append(_row_to_tuple(row))
    return rows


def load_dataset(filename: str = "diabetic_data.csv") -> int:
    """
    Load encounters from data/<filename> into patient_encounters.

    risk_score and risk_level are left NULL — score them later in service.py
    without using readmitted.
    """
    csv_path = DATA_DIR / filename
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    print(f"Reading {csv_path} ...")
    rows = read_encounter_rows(csv_path)
    print(f"Parsed {len(rows):,} rows. Clearing existing tables and inserting ...")

    repository.clear_encounter_tables()
    inserted = repository.bulk_insert_encounters(rows)
    print(f"Inserted {inserted:,} encounters into patient_encounters.")
    return inserted


if __name__ == "__main__":
    load_dataset()
