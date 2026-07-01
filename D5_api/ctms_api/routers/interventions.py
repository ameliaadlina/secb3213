"""
Owner: Member A — Trials & Interventions
Covers AR9 (interventions by gene/protein target).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from db import interventions as interventions_col
from schemas import Envelope, paginate, pagination_params

router = APIRouter()


# ---------------------------------------------------------------------
# AR9 — Interventions targeting a specified gene symbol or protein,
# including their trial context and regulatory status.
# GET /api/interventions?target_gene=EGFR
# GET /api/interventions?target_protein=PD-1
# ---------------------------------------------------------------------
@router.get("/api/interventions", response_model=Envelope)
def list_interventions(
    target_gene: Optional[str] = Query(None, description="e.g. EGFR, BRCA1, TP53"),
    target_protein: Optional[str] = Query(None, description="e.g. PD-1"),
    regulatory_status: Optional[str] = Query(None),
    pagination: dict = Depends(pagination_params),
):
    if not target_gene and not target_protein:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of target_gene or target_protein",
        )

    mongo_filter = {}
    if target_gene:
        mongo_filter["target_gene"] = {"$regex": f"^{target_gene}$", "$options": "i"}
    if target_protein:
        mongo_filter["target_protein"] = {"$regex": target_protein, "$options": "i"}
    if regulatory_status:
        mongo_filter["regulatory_status"] = regulatory_status

    # TODO (Member A): "including their associated trial context" — this
    # likely needs a $lookup into clinical_trials on trial_id to pull in
    # title/phase/status alongside each intervention. A plain find() is
    # the minimum; add the $lookup with an aggregate() pipeline for full marks.
    cursor = interventions_col.find(mongo_filter)
    return paginate(cursor, interventions_col, mongo_filter, pagination["page"], pagination["limit"])


@router.get("/api/interventions/{intervention_id}")
def get_intervention(intervention_id: str):
    doc = interventions_col.find_one({"intervention_id": intervention_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Intervention '{intervention_id}' not found")
    doc["_id"] = str(doc["_id"])
    return doc
