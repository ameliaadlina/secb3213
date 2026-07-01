"""
Owner: Member C — Adverse Events
Covers AR4 (AEs for a patient), AR5 (AE summary by intervention type),
AR7 (causality-severity matrix), AR10 (monthly AE trend).

Reminder from the brief: an AE does not carry arm_label directly — to
get from an AE to its arm, look up the intervention it references
(intervention.arm_label). Relevant for any arm-level breakdown.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from db import adverse_events as ae_col
from schemas import Envelope, paginate, pagination_params

router = APIRouter()


# ---------------------------------------------------------------------
# AR4 — All adverse events for a patient, filterable by severity etc.
# GET /api/patients/{patient_id}/adverse-events?ctcae_grade=3
# ---------------------------------------------------------------------
@router.get("/api/patients/{patient_id}/adverse-events", response_model=Envelope)
def adverse_events_for_patient(
    patient_id: str,
    ctcae_grade: Optional[int] = Query(None, ge=1, le=5),
    serious: Optional[bool] = Query(None),
    outcome: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    mongo_filter = {"patient_id": patient_id}
    if ctcae_grade is not None:
        mongo_filter["ctcae_grade"] = ctcae_grade
    if serious is not None:
        mongo_filter["serious"] = serious
    if outcome:
        mongo_filter["outcome"] = outcome

    cursor = ae_col.find(mongo_filter)
    return paginate(cursor, ae_col, mongo_filter, pagination["page"], pagination["limit"])


# ---------------------------------------------------------------------
# AR5 — AE summary grouped by intervention type: counts + proportion
# serious per type.
# GET /api/adverse-events/summary-by-intervention-type
#
# TODO (Member C): AE -> intervention_id -> interventions.type, so this
# needs a $lookup into interventions before grouping. Sketch:
#   1. $lookup interventions on intervention_id -> intervention_doc
#   2. $unwind intervention_doc
#   3. $group by intervention_doc.type: total_ae, serious_ae (sum of serious==true)
#   4. $addFields serious_proportion = serious_ae / total_ae
# ---------------------------------------------------------------------
@router.get("/api/adverse-events/summary-by-intervention-type", response_model=Envelope)
def ae_summary_by_intervention_type(
    pagination: dict = Depends(pagination_params),
):
    raise HTTPException(status_code=501, detail="TODO: implement AR5 aggregation pipeline")


# ---------------------------------------------------------------------
# AR7 — AE causality x CTCAE grade cross-tab, for a given trial.
# GET /api/trials/{trial_id}/adverse-events/causality-matrix
#
# TODO (Member C): $match trial_id, then $group by
# {causality, ctcae_grade} with a count, and reshape into a matrix
# (causality rows x grade columns) either in the pipeline via
# $group -> $push, or in Python after aggregate() returns.
# ---------------------------------------------------------------------
@router.get("/api/trials/{trial_id}/adverse-events/causality-matrix")
def causality_severity_matrix(trial_id: str):
    raise HTTPException(status_code=501, detail="TODO: implement AR7 aggregation pipeline")


# ---------------------------------------------------------------------
# AR10 — Monthly AE trend, optionally scoped to a trial or intervention
# type.
# GET /api/adverse-events/monthly-trend?trial_id=NCT-20240001
# GET /api/adverse-events/monthly-trend?intervention_type=Drug
#
# TODO (Member C): group by {$year: "$onset_date", $month: "$onset_date"}.
# Filtering by intervention_type again needs the $lookup into
# interventions first, same as AR5.
# ---------------------------------------------------------------------
@router.get("/api/adverse-events/monthly-trend", response_model=Envelope)
def monthly_ae_trend(
    trial_id: Optional[str] = Query(None),
    intervention_type: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    raise HTTPException(status_code=501, detail="TODO: implement AR10 aggregation pipeline")
