"""
Owner: Member C — Adverse Events

Reads raw_data/ctms_adverse_events.csv, transforms each row into the D1
adverse_events schema shape (nests lab_* columns into a lab_values object,
or null if no lab data was recorded for that row), and inserts into
MongoDB.

Must run LAST — after patients, clinical_trials, and interventions are all
loaded — since every adverse_events document carries mandatory references
(patient_id, trial_id, intervention_id) to those three collections. This
script checks those references exist before inserting and prints a
warning for any that don't, rather than failing silently.

Usage:
    python ingest_adverse_events.py
"""
import os
import sys

from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME, SCHEMA_DIR
from csv_utils import read_csv, parse_date, parse_int, parse_float, parse_bool, none_if_empty
from mongo_utils import get_validator, ensure_collection, print_samples

COLLECTION_NAME = "adverse_events"
RAW_CSV = os.path.join(os.path.dirname(__file__), "raw_data", "ctms_adverse_events.csv")


def transform(row: dict) -> dict:
    has_lab_data = any([row["lab_test_name"], row["lab_value"], row["lab_unit"], row["lab_reference_range"]])
    lab_values = None
    if has_lab_data:
        lab_values = {
            "test_name": none_if_empty(row["lab_test_name"]),
            "value": parse_float(row["lab_value"]),
            "unit": none_if_empty(row["lab_unit"]),
            "reference_range": none_if_empty(row["lab_reference_range"]),
        }

    return {
        "ae_id": row["ae_id"],
        "patient_id": row["patient_id"],
        "trial_id": row["trial_id"],
        "intervention_id": row["intervention_id"],
        "event_name": row["event_name"],
        "system_organ_class": row["system_organ_class"],
        "ctcae_grade": parse_int(row["ctcae_grade"]),
        "onset_date": parse_date(row["onset_date"]),
        "resolution_date": parse_date(row["resolution_date"]),
        "outcome": row["outcome"],
        "serious": parse_bool(row["serious"]),
        "action_taken": row["action_taken"],
        "causality": row["causality"],
        "lab_values": lab_values,
        "reported_by": row["reported_by"],
        "created_at": parse_date(row["created_at"]),
    }


def check_referential_integrity(db, docs: list[dict]):
    """Warn (don't fail) if any AE references an ID missing from its collection."""
    patient_ids = set(db["patients"].distinct("patient_id"))
    trial_ids = set(db["clinical_trials"].distinct("trial_id"))
    intervention_ids = set(db["interventions"].distinct("intervention_id"))

    missing = {"patient_id": 0, "trial_id": 0, "intervention_id": 0}
    for doc in docs:
        if doc["patient_id"] not in patient_ids:
            missing["patient_id"] += 1
        if doc["trial_id"] not in trial_ids:
            missing["trial_id"] += 1
        if doc["intervention_id"] not in intervention_ids:
            missing["intervention_id"] += 1

    if any(missing.values()):
        print(f"WARNING — dangling references found: {missing}")
        print("Make sure ingest_patients.py, ingest_trials.py, and "
              "ingest_interventions.py have all been run first.")
    else:
        print("Referential integrity check passed: all patient_id / trial_id / "
              "intervention_id references resolve correctly.")


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    validator = get_validator(SCHEMA_DIR, "adverse_events_schema.json")
    ensure_collection(db, COLLECTION_NAME, validator)

    raw_rows = read_csv(RAW_CSV)
    docs = [transform(row) for row in raw_rows]

    check_referential_integrity(db, docs)

    result = db[COLLECTION_NAME].insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into '{COLLECTION_NAME}' "
          f"(from {len(raw_rows)} rows in {os.path.basename(RAW_CSV)}).")
    print_samples(db, COLLECTION_NAME)

    client.close()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
