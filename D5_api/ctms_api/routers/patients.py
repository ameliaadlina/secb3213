"""
Owner: Member B — Patients & Sites
Covers AR2 (patients for a trial), AR3 (search patients), AR8 (site-level
enrolment / AE burden).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from db import patients as patients_col, adverse_events as ae_col
from schemas import Envelope, paginate, pagination_params

router = APIRouter()


# ---------------------------------------------------------------------
# AR3 — Search patients by demographic / clinical criteria.
# GET /api/patients?gender=Female&ethnicity=Malay&site_id=SITE-02
# ---------------------------------------------------------------------
@router.get("/api/patients", response_model=Envelope)
def search_patients(
    gender: Optional[str] = Query(None),
    ethnicity: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    diagnosis: Optional[str] = Query(None, description="Matches diagnosis.description"),
    pagination: dict = Depends(pagination_params),
):
    mongo_filter = {}
    if gender:
        mongo_filter["gender"] = gender
    if ethnicity:
        mongo_filter["ethnicity"] = ethnicity
    if site_id:
        mongo_filter["site_id"] = site_id
    if diagnosis:
        mongo_filter["diagnosis.description"] = {"$regex": diagnosis, "$options": "i"}

    cursor = patients_col.find(mongo_filter)
    return paginate(cursor, patients_col, mongo_filter, pagination["page"], pagination["limit"])


@router.get("/api/patients/{patient_id}")
def get_patient(patient_id: str):
    doc = patients_col.find_one({"patient_id": patient_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    doc["_id"] = str(doc["_id"])
    return doc


# ---------------------------------------------------------------------
# AR2 — Given a trial, retrieve demographics of all enrolled patients,
# narrowable by patient attributes. Nested under /trials/ since it's
# scoped by trial_id (required path param) — lives here because it
# queries the patients collection.
# GET /api/trials/{trial_id}/patients?gender=Male&ethnicity=Chinese
#
# TODO (Member B): patients.enrolled_trials is an array of trial_id
# strings, so the match is `{"enrolled_trials": trial_id, ...filters}`.
# ---------------------------------------------------------------------
@router.get("/api/trials/{trial_id}/patients", response_model=Envelope)
def patients_for_trial(
    trial_id: str,
    gender: Optional[str] = Query(None),
    ethnicity: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    mongo_filter = {"enrolled_trials": trial_id}
    if gender:
        mongo_filter["gender"] = gender
    if ethnicity:
        mongo_filter["ethnicity"] = ethnicity

    cursor = patients_col.find(mongo_filter)
    return paginate(cursor, patients_col, mongo_filter, pagination["page"], pagination["limit"])


# ---------------------------------------------------------------------
# AR8 — Site-level enrolment and AE burden: for each site, return
# patient count and their total/serious AE counts.
# GET /api/sites/enrolment-ae-burden
#
# TODO (Member B): this needs a $lookup from patients into
# adverse_events (join on patient_id), then $group by site_id counting
# patients, total AEs, and AEs where serious == true. Sketch:
#   1. $group patients by site_id -> patient_count, patient_ids array
#   2. $lookup adverse_events where patient_id in patient_ids
#   3. $addFields total_ae = size(lookup), serious_ae = count where serious
# ---------------------------------------------------------------------
@router.get("/api/sites/enrolment-ae-burden", response_model=Envelope)
def site_enrolment_ae_burden(
    pagination: dict = Depends(pagination_params),
):
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

    all_data = list(patients_col.aggregate(pipeline))
    total = len(all_data)

    page = pagination["page"]
    limit = pagination["limit"]
    skip = (page - 1) * limit
    data = all_data[skip: skip + limit]

    return Envelope(total=total, page=page, limit=limit, data=data)