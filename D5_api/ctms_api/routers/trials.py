"""
Owner: Member A — Trials & Interventions
Covers AR1 (filter trials) and AR6 (enrolment progress).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from db import trials as trials_col
from schemas import Envelope, paginate, pagination_params

router = APIRouter()


# ---------------------------------------------------------------------
# AR1 — Filter trials by status and/or phase (and/or sponsor)
# GET /api/trials?status=Recruiting&phase=Phase III&sponsor=MCRI&page=1&limit=20
# ---------------------------------------------------------------------
@router.get("/api/trials", response_model=Envelope)
def list_trials(
    status: Optional[str] = Query(None, description="e.g. Recruiting, Completed"),
    phase: Optional[str] = Query(None, description="e.g. Phase I, Phase III"),
    sponsor: Optional[str] = Query(None, description="Exact or partial sponsor name"),
    pagination: dict = Depends(pagination_params),
):
    mongo_filter = {}
    if status:
        mongo_filter["status"] = status
    if phase:
        mongo_filter["phase"] = phase
    if sponsor:
        mongo_filter["sponsor"] = {"$regex": sponsor, "$options": "i"}

    cursor = trials_col.find(mongo_filter)
    return paginate(cursor, trials_col, mongo_filter, pagination["page"], pagination["limit"])


# ---------------------------------------------------------------------
# AR6 — Enrolment progress across trials, filterable by sponsor/phase.
# GET /api/trials/enrolment-progress?sponsor=MCRI&phase=Phase II
#
# IMPORTANT: this must be registered BEFORE /api/trials/{trial_id} below.
# FastAPI matches routes in registration order, and {trial_id} is a
# catch-all path param — if it came first, a request to this URL would
# match {trial_id}="enrolment-progress" instead, look for a trial with
# that literal ID, find none, and 404. Static paths always go before
# dynamic path-param routes on the same prefix.
# ---------------------------------------------------------------------
@router.get("/api/trials/enrolment-progress", response_model=Envelope)
def enrolment_progress(
    sponsor: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    match_stage = {}
    if sponsor:
        match_stage["sponsor"] = {"$regex": sponsor, "$options": "i"}
    if phase:
        match_stage["phase"] = phase

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
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
    ]
    total = trials_col.count_documents(match_stage)
    skip = (pagination["page"] - 1) * pagination["limit"]
    data = list(trials_col.aggregate(pipeline + [{"$skip": skip}, {"$limit": pagination["limit"]}]))
    return Envelope(total=total, page=pagination["page"], limit=pagination["limit"], data=data)


# ---------------------------------------------------------------------
# Single trial by ID — required identifier, so it's a path param.
# GET /api/trials/{trial_id}
# Registered AFTER enrolment-progress — see note above.
# ---------------------------------------------------------------------
@router.get("/api/trials/{trial_id}")
def get_trial(trial_id: str):
    trial = trials_col.find_one({"trial_id": trial_id})
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial '{trial_id}' not found")
    trial["_id"] = str(trial["_id"])
    return trial
