"""Portal-side config — separate from the API's config.py."""
import os

API_BASE_URL = os.getenv("CTMS_API_BASE_URL", "http://127.0.0.1:8000")
