"""
Shared connection settings for D2 ingestion scripts. Kept standalone
(not importing from D5_api/ctms_api) since D2_ingestion is meant to be
runnable independently, before the API even exists.
"""
import os
from dotenv import load_dotenv

# Loads variables from a .env file at the project root (SECB3213/.env)
# into the environment. Safe to call even if the file doesn't exist yet —
# falls back to the os.getenv() defaults below.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGO_URI = os.getenv("CTMS_MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("CTMS_DB_NAME", "ctms")

# Path to the D1 schema files, relative to this file, used to apply
# MongoDB validators when (re)creating collections.
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "D1_schemas")
