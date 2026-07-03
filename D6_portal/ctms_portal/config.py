"""Portal-side config — separate from the API's config.py."""
import os
from dotenv import load_dotenv

# SECB3213/D6_portal/ctms_portal/config.py -> project root is two levels up.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

API_BASE_URL = os.getenv("CTMS_API_BASE_URL", "http://127.0.0.1:8000")
