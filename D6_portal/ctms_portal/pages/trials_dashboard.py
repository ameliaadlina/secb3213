"""
Owner: Member A — Trials & Interventions
Portal features: trial browser (AR1), enrolment dashboard (AR6),
gene/target search (AR9).
"""
import streamlit as st
from api_client import api_get


def render():
    st.header("Trials & Interventions")

    # TODO (Member A): AR1 — trial browser
    # Example wiring:
    #   status = st.selectbox("Status", ["", "Recruiting", "Completed", ...])
    #   phase = st.selectbox("Phase", ["", "Phase I", "Phase II", ...])
    #   result = api_get("/api/trials", params={"status": status, "phase": phase})
    #   if result: st.dataframe(result["data"])
    st.info("TODO: trial browser (AR1)")

    # TODO (Member A): AR6 — enrolment progress dashboard
    #   result = api_get("/api/trials/enrolment-progress", params={"sponsor": sponsor})
    #   st.bar_chart(...) on enrolment_pct
    st.info("TODO: enrolment progress dashboard (AR6)")

    # TODO (Member A): AR9 — interventions by gene/protein target
    #   gene = st.text_input("Gene symbol (e.g. EGFR)")
    #   result = api_get("/api/interventions", params={"target_gene": gene})
    st.info("TODO: gene/target search (AR9)")
