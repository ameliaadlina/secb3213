"""
Owner: Member C — Adverse Events

Covers:
AR4  - Retrieve all adverse events for a patient
AR5  - AE summary grouped by intervention type
AR7  - AE causality-severity matrix for a trial
AR10 - Monthly AE trend over time
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from db import adverse_events as ae_col
from schemas import Envelope, paginate, pagination_params

router = APIRouter()


# ---------------------------------------------------------------------
# Helper for aggregation endpoints that return Envelope format
# ---------------------------------------------------------------------
def aggregate_with_envelope(collection, pipeline, page: int, limit: int, sort_stage: dict | None = None):
    count_result = list(collection.aggregate(pipeline + [{"$count": "total"}]))
    total = count_result[0]["total"] if count_result else 0

    skip = (page - 1) * limit

    final_pipeline = pipeline.copy()
    if sort_stage:
        final_pipeline.append(sort_stage)

    final_pipeline.extend([
        {"$skip": skip},
        {"$limit": limit}
    ])

    data = list(collection.aggregate(final_pipeline))

    return Envelope(
        total=total,
        page=page,
        limit=limit,
        data=data
    )


# ---------------------------------------------------------------------
# AR4 — Retrieve all adverse events for a patient
# GET /api/patients/{patient_id}/adverse-events?ctcae_grade=3&serious=true
# ---------------------------------------------------------------------
@router.get("/api/patients/{patient_id}/adverse-events", response_model=Envelope)
def adverse_events_for_patient(
    patient_id: str,
    ctcae_grade: Optional[int] = Query(None, ge=1, le=5),
    serious: Optional[bool] = Query(None),
    outcome: Optional[str] = Query(None),
    causality: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    mongo_filter = {"patient_id": patient_id}

    if ctcae_grade is not None:
        mongo_filter["ctcae_grade"] = ctcae_grade

    if serious is not None:
        mongo_filter["serious"] = serious

    if outcome:
        mongo_filter["outcome"] = outcome

    if causality:
        mongo_filter["causality"] = causality

    cursor = ae_col.find(mongo_filter).sort("onset_date", -1)

    return paginate(
        cursor,
        ae_col,
        mongo_filter,
        pagination["page"],
        pagination["limit"]
    )


# ---------------------------------------------------------------------
# AR5 — AE summary grouped by intervention type
# GET /api/adverse-events/summary-by-intervention-type
# Optional: ?trial_id=NCT-20240005
# ---------------------------------------------------------------------
@router.get("/api/adverse-events/summary-by-intervention-type", response_model=Envelope)
def ae_summary_by_intervention_type(
    trial_id: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
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
        }
    ]

    return aggregate_with_envelope(
        ae_col,
        pipeline,
        pagination["page"],
        pagination["limit"],
        {"$sort": {"total_ae": -1}}
    )


# ---------------------------------------------------------------------
# AR7 — AE causality-severity matrix for a trial
# GET /api/trials/{trial_id}/adverse-events/causality-matrix
# ---------------------------------------------------------------------
@router.get("/api/trials/{trial_id}/adverse-events/causality-matrix", response_model=Envelope)
def causality_severity_matrix(
    trial_id: str,
    pagination: dict = Depends(pagination_params),
):
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

    grouped_results = list(ae_col.aggregate(pipeline))

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

    data_all = [row for row in matrix.values() if row["total"] > 0]

    total = len(data_all)
    skip = (pagination["page"] - 1) * pagination["limit"]
    data = data_all[skip: skip + pagination["limit"]]

    return Envelope(
        total=total,
        page=pagination["page"],
        limit=pagination["limit"],
        data=data
    )


# ---------------------------------------------------------------------
# AR10 — Monthly AE trend over time
# GET /api/adverse-events/monthly-trend
# Optional:
# /api/adverse-events/monthly-trend?trial_id=NCT-20240005
# /api/adverse-events/monthly-trend?intervention_type=Drug
# ---------------------------------------------------------------------
@router.get("/api/adverse-events/monthly-trend", response_model=Envelope)
def monthly_ae_trend(
    trial_id: Optional[str] = Query(None),
    intervention_type: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
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
        }
    ])

    return aggregate_with_envelope(
        ae_col,
        pipeline,
        pagination["page"],
        pagination["limit"],
        {"$sort": {"year": 1, "month": 1}}
    )