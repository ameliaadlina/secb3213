"""
Owner: Member A — Trials & Interventions

Reads raw_data/ctms_trials.csv, transforms each row into the D1
clinical_trials schema shape, and inserts into MongoDB. Applies the D1
JSON Schema as a MongoDB validator.

trials.csv has no `interventions` column — that array is derived by
reading ctms_interventions.csv separately and grouping intervention_ids
by trial_id, so it gets backfilled here even though this script's main
job is "just" the trials collection.

Usage:
    python ingest_trials.py
"""
import os
import sys

from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME, SCHEMA_DIR
from csv_utils import read_csv, split_pipe, parse_date, parse_arms
from mongo_utils import get_validator, ensure_collection, print_samples

COLLECTION_NAME = "clinical_trials"
RAW_CSV = os.path.join(os.path.dirname(__file__), "raw_data", "ctms_trials.csv")
INTERVENTIONS_CSV = os.path.join(os.path.dirname(__file__), "raw_data", "ctms_interventions.csv")


def load_interventions_by_trial() -> dict:
    """Group ctms_interventions.csv's intervention_ids by trial_id."""
    grouped = {}
    for row in read_csv(INTERVENTIONS_CSV):
        grouped.setdefault(row["trial_id"], []).append(row["intervention_id"])
    return grouped


def transform(row: dict, interventions_by_trial: dict) -> dict:
    return {
        "trial_id": row["trial_id"],
        "title": row["title"],
        "short_title": row["short_title"],
        "phase": row["phase"],
        "status": row["status"],
        "sponsor": row["sponsor"],
        "conditions": split_pipe(row["conditions"]),
        "interventions": interventions_by_trial.get(row["trial_id"], []),
        "start_date": parse_date(row["start_date"]),
        "estimated_end_date": parse_date(row["estimated_end_date"]),
        "enrolment_target": int(row["enrolment_target"]),
        "enrolled_count": int(row["enrolled_count"]),
        "arms": parse_arms(row["arms"]),
        "primary_endpoint": row["primary_endpoint"],
        "secondary_endpoints": split_pipe(row["secondary_endpoints"]),
        "sites": split_pipe(row["sites"]),
        "ethical_approval": {
            "approval_id": row["ethical_approval_id"],
            "committee": row["ethical_committee"],
            "approved_on": parse_date(row["ethical_approved_on"]),
        },
        "created_at": parse_date(row["created_at"]),
    }


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    validator = get_validator(SCHEMA_DIR, "clinical_trials_schema.json")
    ensure_collection(db, COLLECTION_NAME, validator)

    interventions_by_trial = load_interventions_by_trial()
    raw_rows = read_csv(RAW_CSV)
    docs = [transform(row, interventions_by_trial) for row in raw_rows]

    result = db[COLLECTION_NAME].insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into '{COLLECTION_NAME}' "
          f"(from {len(raw_rows)} rows in {os.path.basename(RAW_CSV)}).")
    print_samples(db, COLLECTION_NAME)

    client.close()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
