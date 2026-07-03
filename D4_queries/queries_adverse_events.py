"""
Owner: Member C — Adverse Events
D4 — Queries & Results for AR4, AR5, AR7, AR10.

Run with:
    python D4_queries/queries_adverse_events.py
"""
import json
from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME


def print_header(ar_id: str, title: str):
    print("=" * 70)
    print(f"{ar_id} — {title}")
    print("=" * 70)


def print_json(label: str, obj):
    print(f"\n{label}:")
    print(json.dumps(obj, indent=2, default=str))


# ---------------------------------------------------------------------
# AR4 — Retrieve all adverse events for a patient
# ---------------------------------------------------------------------
def ar4_adverse_events_for_patient(
    db,
    patient_id,
    ctcae_grade=None,
    serious=None,
    outcome=None,
    causality=None
):
    query = {"patient_id": patient_id}

    if ctcae_grade is not None:
        query["ctcae_grade"] = ctcae_grade

    if serious is not None:
        query["serious"] = serious

    if outcome:
        query["outcome"] = outcome

    if causality:
        query["causality"] = causality

    results = list(
        db["adverse_events"]
        .find(query, {"_id": 0})
        .sort("onset_date", -1)
    )

    return query, results


def run_ar4(db):
    print_header("AR4", "Retrieve all adverse events for a patient")

    example_patient_id = "PT-000001"

    query, results = ar4_adverse_events_for_patient(
        db,
        patient_id=example_patient_id
    )

    print(f"\nWhat it retrieves: all adverse events recorded for patient {example_patient_id}.")
    print_json("MongoDB query", query)
    print_json(f"Result — {len(results)} adverse event(s)", results)

    print(
        "\nExplanation: This query searches the adverse_events collection using "
        "patient_id. Optional filters such as ctcae_grade, serious, outcome, "
        "and causality can be added to narrow the results."
    )
    print()


# ---------------------------------------------------------------------
# AR5 — AE summary grouped by intervention type
# ---------------------------------------------------------------------
def ar5_summary_by_intervention_type(db, trial_id=None):
    match_stage = {}

    if trial_id:
        match_stage["trial_id"] = trial_id

    pipeline = [
        {"$match": match_stage},
        {
            "$lookup": {
                "from": "interventions",
                "localField": "intervention_id",
                "foreignField": "intervention_id",
                "as": "intervention_doc"
            }
        },
        {"$unwind": "$intervention_doc"},
        {
            "$group": {
                "_id": "$intervention_doc.type",
                "total_ae": {"$sum": 1},
                "serious_ae": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$serious", True]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$addFields": {
                "serious_proportion": {
                    "$round": [
                        {"$divide": ["$serious_ae", "$total_ae"]},
                        3
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "intervention_type": "$_id",
                "total_ae": 1,
                "serious_ae": 1,
                "serious_proportion": 1
            }
        },
        {"$sort": {"total_ae": -1}}
    ]

    results = list(db["adverse_events"].aggregate(pipeline))

    return pipeline, results


def run_ar5(db):
    print_header("AR5", "AE summary grouped by intervention type")

    pipeline, results = ar5_summary_by_intervention_type(db)

    print(
        "\nWhat it retrieves: total adverse events and serious adverse events "
        "grouped by intervention type."
    )
    print_json("MongoDB aggregation pipeline", pipeline)
    print_json(f"Result — {len(results)} intervention type(s)", results)

    print(
        "\nExplanation: The adverse_events collection only stores intervention_id. "
        "Therefore, this pipeline uses $lookup to join with the interventions "
        "collection, then groups the adverse events by intervention type."
    )
    print()


# ---------------------------------------------------------------------
# AR7 — AE causality-severity matrix for a trial
# ---------------------------------------------------------------------
def ar7_causality_severity_matrix(db, trial_id):
    pipeline = [
        {"$match": {"trial_id": trial_id}},
        {
            "$group": {
                "_id": {
                    "causality": "$causality",
                    "ctcae_grade": "$ctcae_grade"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "causality": "$_id.causality",
                "ctcae_grade": "$_id.ctcae_grade",
                "count": 1
            }
        },
        {"$sort": {"causality": 1, "ctcae_grade": 1}}
    ]

    grouped_results = list(db["adverse_events"].aggregate(pipeline))

    causality_order = ["Unrelated", "Unlikely", "Possible", "Probable", "Definite"]

    matrix = {
        causality: {
            "causality": causality,
            "grade_1": 0,
            "grade_2": 0,
            "grade_3": 0,
            "grade_4": 0,
            "grade_5": 0,
            "total": 0
        }
        for causality in causality_order
    }

    for row in grouped_results:
        causality = row["causality"]
        grade = row["ctcae_grade"]
        count = row["count"]

        if causality not in matrix:
            matrix[causality] = {
                "causality": causality,
                "grade_1": 0,
                "grade_2": 0,
                "grade_3": 0,
                "grade_4": 0,
                "grade_5": 0,
                "total": 0
            }

        matrix[causality][f"grade_{grade}"] = count
        matrix[causality]["total"] += count

    matrix_result = [row for row in matrix.values() if row["total"] > 0]

    return pipeline, grouped_results, matrix_result


def run_ar7(db):
    print_header("AR7", "AE causality-severity matrix for a trial")

    example_trial_id = "NCT-20240005"

    pipeline, grouped_results, matrix_result = ar7_causality_severity_matrix(
        db,
        trial_id=example_trial_id
    )

    print(
        f"\nWhat it retrieves: adverse events for trial {example_trial_id}, "
        "cross-tabulated by causality and CTCAE grade."
    )
    print_json("MongoDB aggregation pipeline", pipeline)
    print_json("Intermediate grouped result", grouped_results)
    print_json("Final matrix result", matrix_result)

    print(
        "\nExplanation: This pipeline first groups adverse events by causality "
        "and CTCAE grade. The Python code then reshapes the grouped result into "
        "a matrix format that is easier to display in the portal."
    )
    print()


# ---------------------------------------------------------------------
# AR10 — Monthly AE trend over time
# ---------------------------------------------------------------------
def ar10_monthly_ae_trend(db, trial_id=None, intervention_type=None):
    pipeline = []

    if trial_id:
        pipeline.append({"$match": {"trial_id": trial_id}})

    if intervention_type:
        pipeline.extend([
            {
                "$lookup": {
                    "from": "interventions",
                    "localField": "intervention_id",
                    "foreignField": "intervention_id",
                    "as": "intervention_doc"
                }
            },
            {"$unwind": "$intervention_doc"},
            {"$match": {"intervention_doc.type": intervention_type}}
        ])

    pipeline.extend([
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$onset_date"},
                    "month": {"$month": "$onset_date"}
                },
                "ae_count": {"$sum": 1},
                "serious_ae_count": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$serious", True]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id.year",
                "month": "$_id.month",
                "ae_count": 1,
                "serious_ae_count": 1
            }
        },
        {"$sort": {"year": 1, "month": 1}}
    ])

    results = list(db["adverse_events"].aggregate(pipeline))

    return pipeline, results


def run_ar10(db):
    print_header("AR10", "Monthly AE trend over time")

    example_trial_id = "NCT-20240005"

    pipeline, results = ar10_monthly_ae_trend(
        db,
        trial_id=example_trial_id
    )

    print(
        f"\nWhat it retrieves: monthly adverse event counts for trial "
        f"{example_trial_id}, grouped by year and month."
    )
    print_json("MongoDB aggregation pipeline", pipeline)
    print_json(f"Result — {len(results)} month(s)", results)

    print(
        "\nExplanation: This pipeline groups adverse events by the year and "
        "month of onset_date. It also counts serious adverse events separately. "
        "The output can be used to plot a monthly adverse event trend chart."
    )
    print()


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    run_ar4(db)
    run_ar5(db)
    run_ar7(db)
    run_ar10(db)

    client.close()


if __name__ == "__main__":
    main()