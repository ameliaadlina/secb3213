# CTMS — Clinical Trial Management System

Group project for SECB3213 — Mini Project. Meridian Clinical Research Institute (MCRI) CTMS
prototype: MongoDB + FastAPI + Streamlit/Gradio.

**Team**
| Member | Domain | Collections | ARs |
|---|---|---|---|
| A — Amelia| Trials & Interventions | `clinical_trials`, `interventions` | AR1, AR6, AR9 |
| B — Hafiz | Patients & Sites | `patients` | AR2, AR3, AR8 |
| C — Ravinesh | Adverse Events | `adverse_events` | AR4, AR5, AR7, AR10 |

---

## Folder structure

```
SECB3213/
├── D1_schemas/                     # MongoDB JSON Schema (.json), one per collection
├── D2_ingestion/                    # pymongo ingestion scripts + sample-doc screenshots
├── D3_backup/                        # mongodump archive (not committed — see below)
├── D4_queries/                        # Query/aggregation code + results for all 10 ARs
├── D5_api/
│   └── ctms_api/                        # FastAPI app — main.py, db.py, schemas.py, config.py, routers/
├── D6_portal/
│   └── ctms_portal/                       # Streamlit portal — app.py, api_client.py, config.py, pages/
├── D7_report/                                # Technical report (PDF)
├── D8_video/                                    # Demo video (not committed — see below)
├── AI_Declaration/                                # AI tool usage declaration
├── .gitignore
└── README.md                                        # this file
```

---

## Setup

### 1. Prerequisites
- Python 3.10+
- MongoDB running locally (`mongodb://localhost:27017`) or an Atlas connection string
- `pip`

### 2. Install dependencies
```bash
cd D5_api/ctms_api
pip install -r requirements.txt
cd ../../D6_portal/ctms_portal
pip install -r requirements.txt
cd ../..
```

### 3. Environment variables
Create a `.env` file at the repo root (never commit this — see `.gitignore`):
```
CTMS_MONGO_URI=mongodb://localhost:27017
CTMS_DB_NAME=ctms
```

### 4. Load the data
The real dataset (10 trials, 20 interventions, 100 patients, 300 adverse events) lives as CSVs in
`D2_ingestion/raw_data/` — already included in this repo. Each `ingest_*.py` script reads its CSV,
transforms it into the D1 schema shape, and inserts it with the matching validator attached.

Run **in this order** — adverse_events references the other three collections, so it must be
loaded last:
```bash
python D2_ingestion/ingest_trials.py
python D2_ingestion/ingest_interventions.py
python D2_ingestion/ingest_patients.py
python D2_ingestion/ingest_adverse_events.py
```
`ingest_adverse_events.py` checks referential integrity before inserting and will warn (not fail)
if any patient_id / trial_id / intervention_id doesn't resolve — that's your signal the other three
scripts haven't been run yet.

### 5. Run the API
```bash
cd D5_api/ctms_api
uvicorn main:app --reload
```
Swagger UI: http://127.0.0.1:8000/docs

### 6. Run the portal
```bash
cd D6_portal/ctms_portal
streamlit run app.py
```

---

## Restoring the database backup (D3)
```bash
mongorestore --uri="mongodb://localhost:27017" --archive=D3_backup/ctms_backup.tar.gz --gzip
```

---

## Git workflow

- `main` is always demo-able — don't push broken code directly to it.
- One feature branch per domain: `feature/trials-api`, `feature/patients-api`, `feature/ae-api`.
- Open a PR back to `main` when your ARs/endpoints/portal features are working; merge early and
  often rather than letting branches diverge for days.
- Shared files (`D5_api/ctms_api/main.py`, `db.py`, `schemas.py`, `D6_portal/ctms_portal/app.py`,
  `api_client.py`) were built together first as the base skeleton — avoid large simultaneous edits
  to these.

## Not committed to git (see `.gitignore`)
- `.env` (Mongo credentials)
- `D3_backup/*.tar.gz` — share via Drive, link here once available: `<link>`
- `D8_video/*.mp4` — share via Drive, link here once available: `<link>`
- `__pycache__/`, `.venv/`, IDE folders

## AI Declaration
See `AI_Declaration/` for the disclosure of any AI-assisted work, per course requirements.
