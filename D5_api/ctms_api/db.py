"""
Single shared MongoDB client. Import the collection handles from here in
every router — do not open a new MongoClient per file, or per request.
"""
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COL_TRIALS, COL_INTERVENTIONS, COL_PATIENTS, COL_ADVERSE_EVENTS

_client = MongoClient(MONGO_URI)
db = _client[DB_NAME]

trials = db[COL_TRIALS]
interventions = db[COL_INTERVENTIONS]
patients = db[COL_PATIENTS]
adverse_events = db[COL_ADVERSE_EVENTS]
