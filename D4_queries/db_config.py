"""Shared connection settings for D4 query scripts."""
import os
from dotenv import load_dotenv

# D4_queries/db_config.py -> project root is one level up.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGO_URI = os.getenv("CTMS_MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("CTMS_DB_NAME", "ctms")
