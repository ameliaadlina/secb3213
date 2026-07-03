"""
Owner: Member A — Trials & Interventions
D4 — Queries & Results for AR1, AR6, AR9.

This is the standalone MongoDB layer, independent of the FastAPI wrapper
in D5_api/ — the brief asks for the raw query/pipeline + a real example
result to be demonstrated on its own, separate from the API. The logic
here matches routers/trials.py and routers/interventions.py, since the
API endpoints are thin wrappers around these same queries.

Run with:
    python queries_trials_interventions.py

Each AR prints:
  1. What it retrieves
  2. The MongoDB query / aggregation pipeline used
  3. A real example result from the actual dataset
  4. A short explanation of what the result means
"""
import json
from pymongo import MongoClient

from db_config import MONGO_URI, DB_NAME


def _print_header(ar_id: str, title: str):
    print("=" * 70)
    print(f"{ar_id} — {title}")
    print("=" * 70)


def _print_json(label: str, obj):
    print(f"\n{label}:")
    print(json.dumps(obj, indent=2, default=str))


# ---------------------------------------------------------------------
# AR1 — Filter trials by status and/or phase (and/or sponsor)
# ---------------------------------------------------------------------
def ar1_filter_trials(db, status=None, phase=None, sponsor=None):
    """Retrieves a list of clinical trials filtered by status/phase/sponsor."""
    query = {}
    if status:
        query["status"] = status
    if phase:
        query["phase"] = phase
    if sponsor:
        query["sponsor"] = {"$regex": sponsor, "$options": "i"}

    results = list(db["clinical_trials"].find(query, {"_id": 0}))
    return query, results


def run_ar1(db):
    _print_header("AR1", "Filter trials by status and/or phase")
    example_status = "Recruiting"
    query, results = ar1_filter_trials(db, status=example_status)

    print(f"\nWhat it retrieves: clinical trials matching status='{example_status}' "
          f"(phase and sponsor are also supported filters, combined with $and semantics).")
    _print_json("MongoDB query (find filter)", query)
    _print_json(f"Result — {len(results)} matching trial(s)", results)
    print(f"\nExplanation: {len(results)} trial(s) in the dataset currently have "
          f"status = '{example_status}'. Each result includes the full trial document "
          f"(arms, sites, ethical approval, etc.) so the portal can render a trial browser "
          f"directly from this query without a second lookup.")
    print()


# ---------------------------------------------------------------------
# AR6 — Enrolment progress across trials, filterable by sponsor/phase
# ---------------------------------------------------------------------
def ar6_enrolment_progress(db, sponsor=None, phase=None):
    """
    Calculates enrolment completion as a percentage of target, per trial.
    Uses an aggregation pipeline since enrolment_pct is a computed field,
    not something stored directly on the document.
    """
    match_stage = {}
    if sponsor:
        match_stage["sponsor"] = {"$regex": sponsor, "$options": "i"}
    if phase:
        match_stage["phase"] = phase

    pipeline = [
        {"$match": match_stage},
        {
            "$project": {
                "_id": 0,
                "trial_id": 1,
                "title": 1,
                "sponsor": 1,
                "phase": 1,
                "enrolled_count": 1,
                "enrolment_target": 1,
                "enrolment_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$enrolled_count", "$enrolment_target"]},
                            100,
                        ]},
                        1,
                    ]
                },
            }
        },
        {"$sort": {"enrolment_pct": -1}},
    ]
    results = list(db["clinical_trials"].aggregate(pipeline))
    return pipeline, results


def run_ar6(db):
    _print_header("AR6", "Enrolment progress across trials")
    pipeline, results = ar6_enrolment_progress(db)

    print("\nWhat it retrieves: every trial's enrolment completion as a percentage of "
          "its target (enrolled_count / enrolment_target * 100), sorted highest first. "
          "Optionally scoped by sponsor or phase via an added $match stage.")
    _print_json("MongoDB aggregation pipeline", pipeline)
    _print_json(f"Result — {len(results)} trial(s)", results)

    if results:
        top = results[0]
        print(f"\nExplanation: '{top['trial_id']}' has the highest enrolment completion "
              f"at {top['enrolment_pct']}% ({top['enrolled_count']} of "
              f"{top['enrolment_target']} target patients). This view lets a coordinator "
              f"spot under-enrolling trials at a glance — anything near the bottom of this "
              f"sorted list may need a recruitment push.")
    print()


# ---------------------------------------------------------------------
# AR9 — Interventions targeting a specified gene symbol or protein
# ---------------------------------------------------------------------
def ar9_interventions_by_target(db, target_gene=None, target_protein=None):
    """
    Retrieves interventions targeting a gene/protein, including trial
    context via $lookup (join) into clinical_trials.
    """
    match_stage = {}
    if target_gene:
        match_stage["target_gene"] = {"$regex": f"^{target_gene}$", "$options": "i"}
    if target_protein:
        match_stage["target_protein"] = {"$regex": target_protein, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {
            "$lookup": {
                "from": "clinical_trials",
                "localField": "trial_id",
                "foreignField": "trial_id",
                "as": "trial_context",
            }
        },
        {"$unwind": "$trial_context"},
        {
            "$project": {
                "_id": 0,
                "intervention_id": 1,
                "name": 1,
                "type": 1,
                "target_gene": 1,
                "target_protein": 1,
                "regulatory_status": 1,
                "trial_id": 1,
                "trial_title": "$trial_context.title",
                "trial_phase": "$trial_context.phase",
                "trial_status": "$trial_context.status",
            }
        },
    ]
    results = list(db["interventions"].aggregate(pipeline))
    return pipeline, results


def run_ar9(db):
    _print_header("AR9", "Interventions by gene or protein target")
    example_gene = "EGFR"
    pipeline, results = ar9_interventions_by_target(db, target_gene=example_gene)

    print(f"\nWhat it retrieves: interventions targeting gene '{example_gene}', joined "
          f"with their parent trial's context (title, phase, status) via $lookup, since "
          f"the brief asks for target interventions 'including their associated trial "
          f"context and regulatory status'.")
    _print_json("MongoDB aggregation pipeline", pipeline)
    _print_json(f"Result — {len(results)} intervention(s)", results)

    if results:
        r = results[0]
        print(f"\nExplanation: '{r['name']}' ({r['intervention_id']}) targets {example_gene} "
              f"and is administered under trial '{r['trial_id']}' ({r['trial_title']}, "
              f"currently {r['trial_status']}). The $lookup join is what makes this AR "
              f"different from a plain filter — without it, the trial context (title, "
              f"phase, status) wouldn't be available in a single query.")
    print()


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    run_ar1(db)
    run_ar6(db)
    run_ar9(db)

    client.close()


if __name__ == "__main__":
    main()
