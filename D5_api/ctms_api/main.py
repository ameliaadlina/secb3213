"""
App shell — build this ONCE as a team before splitting off to build
individual endpoints. Everyone's router plugs in here.

Run with:
    uvicorn main:app --reload
Then open http://127.0.0.1:8000/docs for Swagger UI.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routers import trials, interventions, patients, adverse_events

app = FastAPI(
    title="CTMS API",
    description="Read-only RESTful API for the Meridian Clinical Research Institute CTMS.",
    version="1.0.0",
)

# --- Routers -----------------------------------------------------------
# No shared prefix here on purpose: routes are written with their full
# path inside each router file (e.g. "/api/trials/{trial_id}/patients"
# lives in patients.py). That lets nested resources sit next to the
# collection they actually query, instead of being forced under whichever
# router owns the URL prefix. Keep paths plural, lowercase, hyphenated.
app.include_router(trials.router, tags=["Trials"])
app.include_router(interventions.router, tags=["Interventions"])
app.include_router(patients.router, tags=["Patients"])
app.include_router(adverse_events.router, tags=["Adverse Events"])


# --- Shared error handling ----------------------------------------------
# Individual endpoints should still raise HTTPException(status_code=404, ...)
# for expected cases (e.g. patient not found). This catches anything
# unhandled and returns a consistent 500 shape instead of a raw traceback.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/api/health", tags=["Meta"])
def health_check():
    """Quick liveness check — not one of the 10 ARs, just useful for demoing."""
    return {"status": "ok"}
