"""
Central configuration. Pull from environment variables in production;
hardcoded defaults here are fine for local dev / demo.
"""
import os
from dotenv import load_dotenv

# Loads variables from the .env file at the project root (SECB3213/.env).
# This file sits at SECB3213/D5_api/ctms_api/config.py, so the root is
# two levels up.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

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
