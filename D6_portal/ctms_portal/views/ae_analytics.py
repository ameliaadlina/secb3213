"""
Owner: Member C — Adverse Events
Portal features: AE filter table (AR4/AR5), causality-grade matrix (AR7),
monthly trend chart (AR10).
"""
import streamlit as st
from api_client import api_get


def render():
    st.header("Adverse Events")

    # TODO (Member C): AR4 — AEs for a patient, filterable by severity
    #   patient_id = st.text_input("Patient ID (e.g. PT-001023)")
    #   result = api_get(f"/api/patients/{patient_id}/adverse-events")
    st.info("TODO: AE filter table (AR4 / AR5)")

    # TODO (Member C): AR7 — causality x CTCAE grade matrix for a trial
    #   trial_id = st.text_input("Trial ID")
    #   result = api_get(f"/api/trials/{trial_id}/adverse-events/causality-matrix")
    #   st.dataframe(...) shaped as a matrix
    st.info("TODO: causality-grade matrix (AR7)")

    # TODO (Member C): AR10 — monthly AE trend, optionally scoped
    #   result = api_get("/api/adverse-events/monthly-trend", params={"trial_id": trial_id})
    #   st.line_chart(...)
    st.info("TODO: monthly trend chart (AR10)")
