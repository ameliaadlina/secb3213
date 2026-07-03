"""
Owner: Member B — Patients & Sites
D4 — Queries & Results for AR2, AR3, AR8.

This file demonstrates the raw MongoDB queries / aggregation pipelines
for Member B's analytical requirements.

Run from the project root:
    python D4_queries/queries_patients_sites.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


# Load .env from the project root
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

MONGO_URI = os.getenv("CTMS_MONGO_URI")
DB_NAME = os.getenv("CTMS_DB_NAME", "ctms")


def print_header(ar_id: str, title: str):
    print("=" * 80)
    print(f"{ar_id} — {title}")
    print("=" * 80)


def print_json(label: str, obj):
    print(f"\n{label}:")
    print(json.dumps(obj, indent=2, default=str))


# ---------------------------------------------------------------------
# AR2 — Retrieve all patients for a specific trial
# ---------------------------------------------------------------------
def ar2_patients_for_trial(db, trial_id, gender=None, ethnicity=None):
    """
    Given a trial_id, retrieve all patients enrolled in it.
    Optional filters: gender, ethnicity.
    """
    query = {"enrolled_trials": trial_id}

    if gender:
        query["gender"] = gender

    if ethnicity:
        query["ethnicity"] = ethnicity

    projection = {
        "_id": 0,
        "patient_id": 1,
        "name": 1,
        "gender": 1,
        "ethnicity": 1,
        "site_id": 1,
        "diagnosis": 1,
        "enrolled_trials": 1,
    }

    results = list(db["patients"].find(query, projection))
    return query, results


def run_ar2(db):
    print_header("AR2", "Retrieve all patients for a specific trial")

    example_trial_id = "NCT-20240001"
    query, results = ar2_patients_for_trial(db, trial_id=example_trial_id)

    print(
        f"\nWhat it retrieves: all patients enrolled in trial '{example_trial_id}'. "
        "The query can also be narrowed by gender and ethnicity."
    )
    print_json("MongoDB query", query)
    print_json(f"Result — {len(results)} patient(s)", results)

    print(
        "\nExplanation: The query checks the patients collection and finds documents "
        "where the enrolled_trials array contains the selected trial_id."
    )
    print()


# ---------------------------------------------------------------------
# AR3 — Search patients by demographic or clinical criteria
# ---------------------------------------------------------------------
def ar3_search_patients(db, gender=None, ethnicity=None, site_id=None, diagnosis=None):
    """
    Search patients using demographic or clinical attributes.
    Supported filters: gender, ethnicity, site_id, diagnosis description.
    """
    query = {}

    if gender:
        query["gender"] = gender

    if ethnicity:
        query["ethnicity"] = ethnicity

    if site_id:
        query["site_id"] = site_id

    if diagnosis:
        query["diagnosis.description"] = {"$regex": diagnosis, "$options": "i"}

    projection = {
        "_id": 0,
        "patient_id": 1,
        "name": 1,
        "gender": 1,
        "ethnicity": 1,
        "site_id": 1,
        "blood_type": 1,
        "bmi": 1,
        "smoking_status": 1,
        "diagnosis": 1,
        "enrolled_trials": 1,
    }

    results = list(db["patients"].find(query, projection))
    return query, results


def run_ar3(db):
    print_header("AR3", "Search patients by demographic or clinical criteria")

    example_site = "SITE-01"
    query, results = ar3_search_patients(db, site_id=example_site)

    print(
        f"\nWhat it retrieves: patients from '{example_site}'. "
        "Other supported filters include gender, ethnicity, and diagnosis keyword."
    )
    print_json("MongoDB query", query)
    print_json(f"Result — {len(results)} patient(s)", results)

    print(
        "\nExplanation: This query helps users search the patient population based on "
        "patient attributes such as site, gender, ethnicity, or diagnosis."
    )
    print()


# ---------------------------------------------------------------------
# AR8 — Patient comorbidity and AE burden / site AE burden
# ---------------------------------------------------------------------
def ar8_site_enrolment_ae_burden(db):
    """
    For each site, calculate:
    - number of patients
    - total adverse events
    - serious adverse events
    """
    pipeline = [
        {
            "$group": {
                "_id": "$site_id",
                "patient_count": {"$sum": 1},
                "patient_ids": {"$push": "$patient_id"},
            }
        },
        {
            "$lookup": {
                "from": "adverse_events",
                "localField": "patient_ids",
                "foreignField": "patient_id",
                "as": "adverse_events",
            }
        },
        {
            "$project": {
                "_id": 0,
                "site_id": "$_id",
                "patient_count": 1,
                "total_ae_count": {"$size": "$adverse_events"},
                "serious_ae_count": {
                    "$size": {
                        "$filter": {
                            "input": "$adverse_events",
                            "as": "ae",
                            "cond": {"$eq": ["$$ae.serious", True]},
                        }
                    }
                },
            }
        },
        {"$sort": {"site_id": 1}},
    ]

    results = list(db["patients"].aggregate(pipeline))
    return pipeline, results


def run_ar8(db):
    print_header("AR8", "Site enrolment and adverse event burden")

    pipeline, results = ar8_site_enrolment_ae_burden(db)

    print(
        "\nWhat it retrieves: for each clinical site, the query returns the patient count, "
        "total adverse event count, and serious adverse event count."
    )
    print_json("MongoDB aggregation pipeline", pipeline)
    print_json(f"Result — {len(results)} site(s)", results)

    print(
        "\nExplanation: The pipeline first groups patients by site, then uses $lookup "
        "to connect those patients to their adverse event records. It counts all AEs "
        "and separately counts serious AEs where serious == true."
    )
    print()


def main():
    if not MONGO_URI:
        raise ValueError("CTMS_MONGO_URI is missing. Check your .env file.")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    run_ar2(db)
    run_ar3(db)
    run_ar8(db)

    client.close()


if __name__ == "__main__":
    main()