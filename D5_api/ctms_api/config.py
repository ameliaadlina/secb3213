"""
Central configuration. Pull from environment variables in production;
hardcoded defaults here are fine for local dev / demo.
"""
import os

MONGO_URI = os.getenv("CTMS_MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("CTMS_DB_NAME", "ctms")

# Collection names — keep these as the single source of truth so a rename
# only happens in one place.
COL_TRIALS = "clinical_trials"
COL_INTERVENTIONS = "interventions"
COL_PATIENTS = "patients"
COL_ADVERSE_EVENTS = "adverse_events"

DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
