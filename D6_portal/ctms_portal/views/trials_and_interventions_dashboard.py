"""
Owner: Member A — Trials & Interventions
Portal page covering AR1 (trial browser), AR6 (enrolment progress
dashboard), and AR9 (gene/target search) — the three ARs owned by this
domain, spanning both the clinical_trials and interventions collections.

Renamed from trials_dashboard.py -> trials_and_interventions_dashboard.py
so the filename doesn't read as "trials only" when it also covers AR9,
which queries the interventions collection.
"""
import pandas as pd
import streamlit as st

from api_client import api_get

STATUS_OPTIONS = ["", "Recruiting", "Active (not recruiting)", "Completed",
                   "Terminated", "Suspended", "Withdrawn"]
PHASE_OPTIONS = ["", "Phase I", "Phase II", "Phase III", "Phase IV", "Not Applicable"]


def render():
    st.header("Trials & Interventions")

    tab1, tab2, tab3 = st.tabs([
        "Trial Browser (AR1)",
        "Enrolment Progress (AR6)",
        "Gene / Target Search (AR9)",
    ])

    with tab1:
        render_trial_browser()

    with tab2:
        render_enrolment_progress()

    with tab3:
        render_gene_target_search()


# ---------------------------------------------------------------------
# AR1 — Filter trials by status and/or phase (and/or sponsor)
# ---------------------------------------------------------------------
def render_trial_browser():
    st.subheader("Browse & filter trials")
    st.caption("Calls: GET /api/trials")

    col1, col2, col3 = st.columns(3)
    status = col1.selectbox("Status", STATUS_OPTIONS)
    phase = col2.selectbox("Phase", PHASE_OPTIONS)
    sponsor = col3.text_input("Sponsor (partial match)")

    params = {k: v for k, v in {"status": status, "phase": phase, "sponsor": sponsor}.items() if v}
    result = api_get("/api/trials", params=params)

    if not result:
        return

    st.write(f"**{result['total']}** matching trial(s)")
    if not result["data"]:
        st.info("No trials match these filters.")
        return

    df = pd.DataFrame(result["data"])
    display_cols = ["trial_id", "title", "phase", "status", "sponsor",
                     "enrolled_count", "enrolment_target"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# AR6 — Enrolment progress across trials
# ---------------------------------------------------------------------
def render_enrolment_progress():
    st.subheader("Enrolment completion by trial")
    st.caption("Calls: GET /api/trials/enrolment-progress")

    col1, col2 = st.columns(2)
    sponsor = col1.text_input("Filter by sponsor", key="enrolment_sponsor")
    phase = col2.selectbox("Filter by phase", PHASE_OPTIONS, key="enrolment_phase")

    params = {k: v for k, v in {"sponsor": sponsor, "phase": phase}.items() if v}
    result = api_get("/api/trials/enrolment-progress", params=params)

    if not result:
        return

    st.write(f"**{result['total']}** trial(s)")
    if not result["data"]:
        st.info("No trials match these filters.")
        return

    df = pd.DataFrame(result["data"])
    chart_df = df.set_index("trial_id")[["enrolment_pct"]]
    st.bar_chart(chart_df)

    display_cols = ["trial_id", "title", "sponsor", "phase",
                     "enrolled_count", "enrolment_target", "enrolment_pct"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# AR9 — Interventions by gene or protein target
# ---------------------------------------------------------------------
def render_gene_target_search():
    st.subheader("Find interventions by molecular target")
    st.caption("Calls: GET /api/interventions")

    col1, col2 = st.columns(2)
    target_gene = col1.text_input("Gene symbol (e.g. EGFR, BRCA1, TP53)")
    target_protein = col2.text_input("Protein name (partial match)")

    if not target_gene and not target_protein:
        st.info("Enter a gene symbol or protein name to search.")
        return

    params = {k: v for k, v in {"target_gene": target_gene, "target_protein": target_protein}.items() if v}
    result = api_get("/api/interventions", params=params)

    if not result:
        return

    st.write(f"**{result['total']}** matching intervention(s)")
    if not result["data"]:
        st.info("No interventions target this gene/protein.")
        return

    df = pd.DataFrame(result["data"])
    display_cols = ["intervention_id", "name", "type", "trial_id",
                     "target_gene", "target_protein", "regulatory_status"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
