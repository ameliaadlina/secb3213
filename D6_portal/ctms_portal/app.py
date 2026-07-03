"""
Portal shell — build this ONCE as a team before splitting off to build
individual page features. Everyone's page module plugs in here.

Run with:
    streamlit run app.py
"""
import streamlit as st
from views import trials_and_interventions_dashboard, patients_search, ae_analytics

st.set_page_config(page_title="CTMS Data Portal", layout="wide")

st.sidebar.title("CTMS Data Portal")
st.sidebar.caption("Meridian Clinical Research Institute")

PAGES = {
    "Trials & Interventions": trials_and_interventions_dashboard,
    "Patients & Sites": patients_search,
    "Adverse Events": ae_analytics,
}

selection = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[selection].render()
