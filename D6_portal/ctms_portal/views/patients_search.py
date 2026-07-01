"""
Owner: Member B — Patients & Sites
Portal features: patient search (AR3), trial roster view (AR2),
site AE burden view (AR8).
"""
import streamlit as st
from api_client import api_get


def render():
    st.header("Patients & Sites")

    # TODO (Member B): AR3 — search patients
    #   gender = st.selectbox("Gender", ["", "Male", "Female", ...])
    #   result = api_get("/api/patients", params={"gender": gender})
    st.info("TODO: patient search (AR3)")

    # TODO (Member B): AR2 — patients enrolled in a given trial
    #   trial_id = st.text_input("Trial ID (e.g. NCT-20240001)")
    #   result = api_get(f"/api/trials/{trial_id}/patients")
    st.info("TODO: trial roster view (AR2)")

    # TODO (Member B): AR8 — site-level enrolment / AE burden
    #   result = api_get("/api/sites/enrolment-ae-burden")
    #   st.dataframe(result["data"])
    st.info("TODO: site AE burden view (AR8)")
