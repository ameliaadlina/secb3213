"""
Owner: Member A — Trials & Interventions

Reads raw_data/ctms_interventions.csv, transforms each row into the D1
interventions schema shape (nests the four flat dosage_* columns into one
dosage object), and inserts into MongoDB.

Usage:
    python ingest_interventions.py
"""
import os
import sys

from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME, SCHEMA_DIR
from csv_utils import read_csv, parse_date, parse_int, parse_float, none_if_empty
from mongo_utils import get_validator, ensure_collection, print_samples

COLLECTION_NAME = "interventions"
RAW_CSV = os.path.join(os.path.dirname(__file__), "raw_data", "ctms_interventions.csv")


def transform(row: dict) -> dict:
    return {
        "intervention_id": row["intervention_id"],
        "trial_id": row["trial_id"],
        "arm_label": row["arm_label"],
        "name": row["name"],
        "type": row["type"],
        "mechanism": none_if_empty(row["mechanism"]),
        "dosage": {
            "amount": parse_float(row["dosage_amount"]),
            "unit": row["dosage_unit"],
            "frequency": row["dosage_frequency"],
            "route": row["dosage_route"],
        },
        "duration_weeks": parse_int(row["duration_weeks"]),
        "target_gene": none_if_empty(row["target_gene"]),
        "target_protein": none_if_empty(row["target_protein"]),
        "regulatory_status": row["regulatory_status"],
        "created_at": parse_date(row["created_at"]),
    }


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    validator = get_validator(SCHEMA_DIR, "interventions_schema.json")
    ensure_collection(db, COLLECTION_NAME, validator)

    raw_rows = read_csv(RAW_CSV)
    docs = [transform(row) for row in raw_rows]

    result = db[COLLECTION_NAME].insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into '{COLLECTION_NAME}' "
          f"(from {len(raw_rows)} rows in {os.path.basename(RAW_CSV)}).")
    print_samples(db, COLLECTION_NAME)

    client.close()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
