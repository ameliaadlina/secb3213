"""
Owner: Member B — Patients & Sites

Reads raw_data/ctms_patients.csv, transforms each row into the D1 patients
schema shape (nests diagnosis_* into a diagnosis object, contact_* into a
contact_info object; splits pipe-delimited comorbidities/enrolled_trials
into arrays), and inserts into MongoDB.

Note: the raw CSV includes two extra columns not in the D1 field-level spec
(blood_type, enrolment_date). They're kept as-is since the D1 schema doesn't
forbid additional properties — enrolment_date in particular is useful for
AR-style checks like "AE onset must be after enrolment".

Usage:
    python ingest_patients.py
"""
import os
import sys

from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME, SCHEMA_DIR
from csv_utils import read_csv, split_pipe, parse_date, parse_float, none_if_empty
from mongo_utils import get_validator, ensure_collection, print_samples

COLLECTION_NAME = "patients"
RAW_CSV = os.path.join(os.path.dirname(__file__), "raw_data", "ctms_patients.csv")


def transform(row: dict) -> dict:
    return {
        "patient_id": row["patient_id"],
        "name": row["name"],
        "date_of_birth": parse_date(row["date_of_birth"]),
        "gender": row["gender"],
        "ethnicity": row["ethnicity"],
        "blood_type": none_if_empty(row.get("blood_type", "")),
        "bmi": parse_float(row["bmi"]),
        "smoking_status": row["smoking_status"],
        "diagnosis": {
            "icd10_code": row["diagnosis_icd10"],
            "description": row["diagnosis_desc"],
            "diagnosed_on": parse_date(row["diagnosed_on"]),
        },
        "comorbidities": split_pipe(row["comorbidities"]),
        "site_id": row["site_id"],
        "enrolled_trials": split_pipe(row["enrolled_trials"]),
        "enrolment_date": parse_date(row.get("enrolment_date", "")),
        "contact_info": {
            "email": row["contact_email"],
            "phone": row["contact_phone"],
            "emergency_contact": row["emergency_contact"],
        },
        "created_at": parse_date(row["created_at"]),
    }


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    validator = get_validator(SCHEMA_DIR, "patients_schema.json")
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
