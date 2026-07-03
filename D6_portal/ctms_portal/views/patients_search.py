"""
Owner: Member B — Patients & Sites
Portal features:
- AR3: Search patients by demographic / clinical criteria
- AR2: View patients enrolled in a specific trial
- AR8: Site enrolment and adverse event burden
"""
import pandas as pd
import streamlit as st

from api_client import api_get


GENDER_OPTIONS = ["", "Male", "Female", "Non-binary", "Prefer not to say"]
ETHNICITY_OPTIONS = ["", "Malay", "Chinese", "Indian", "Caucasian", "African", "Hispanic", "Other"]
SITE_OPTIONS = ["", "SITE-01", "SITE-02", "SITE-03", "SITE-04", "SITE-05"]


def render():
    st.header("Patients & Sites")

    tab1, tab2, tab3 = st.tabs([
        "Patient Search (AR3)",
        "Trial Roster (AR2)",
        "Site AE Burden (AR8)",
    ])

    with tab1:
        render_patient_search()

    with tab2:
        render_trial_roster()

    with tab3:
        render_site_ae_burden()


# ---------------------------------------------------------------------
# AR3 — Search patients by gender, ethnicity, site, or diagnosis
# ---------------------------------------------------------------------
def render_patient_search():
    st.subheader("Search patients")
    st.caption("Calls: GET /api/patients")

    col1, col2, col3 = st.columns(3)
    gender = col1.selectbox("Gender", GENDER_OPTIONS)
    ethnicity = col2.selectbox("Ethnicity", ETHNICITY_OPTIONS)
    site_id = col3.selectbox("Site", SITE_OPTIONS)

    diagnosis = st.text_input("Diagnosis keyword, example: NSCLC, Diabetes, Hypertension")

    params = {
        k: v for k, v in {
            "gender": gender,
            "ethnicity": ethnicity,
            "site_id": site_id,
            "diagnosis": diagnosis,
        }.items()
        if v
    }

    result = api_get("/api/patients", params=params)

    if not result:
        return

    st.write(f"**{result['total']}** matching patient(s)")

    if not result["data"]:
        st.info("No patients match these filters.")
        return

    df = pd.DataFrame(result["data"])
    display_cols = [
        "patient_id",
        "name",
        "gender",
        "ethnicity",
        "site_id",
        "blood_type",
        "bmi",
        "smoking_status",
        "enrolled_trials",
    ]
    display_cols = [col for col in display_cols if col in df.columns]

    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# AR2 — Retrieve all patients enrolled in a specific trial
# ---------------------------------------------------------------------
def render_trial_roster():
    st.subheader("Patients enrolled in a trial")
    st.caption("Calls: GET /api/trials/{trial_id}/patients")

    trial_id = st.text_input("Trial ID", value="NCT-20240001")

    col1, col2 = st.columns(2)
    gender = col1.selectbox("Filter by gender", GENDER_OPTIONS, key="trial_gender")
    ethnicity = col2.selectbox("Filter by ethnicity", ETHNICITY_OPTIONS, key="trial_ethnicity")

    if not trial_id:
        st.info("Enter a trial ID to view enrolled patients.")
        return

    params = {
        k: v for k, v in {
            "gender": gender,
            "ethnicity": ethnicity,
        }.items()
        if v
    }

    result = api_get(f"/api/trials/{trial_id}/patients", params=params)

    if not result:
        return

    st.write(f"**{result['total']}** patient(s) enrolled in **{trial_id}**")

    if not result["data"]:
        st.info("No patients found for this trial or filter.")
        return

    df = pd.DataFrame(result["data"])
    display_cols = [
        "patient_id",
        "name",
        "gender",
        "ethnicity",
        "site_id",
        "diagnosis",
        "enrolled_trials",
    ]
    display_cols = [col for col in display_cols if col in df.columns]

    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# AR8 — Site enrolment and adverse event burden
# ---------------------------------------------------------------------
def render_site_ae_burden():
    st.subheader("Site enrolment and AE burden")
    st.caption("Calls: GET /api/sites/enrolment-ae-burden")

    result = api_get("/api/sites/enrolment-ae-burden")

    if not result:
        return

    st.write(f"**{result['total']}** site(s)")

    if not result["data"]:
        st.info("No site burden data found.")
        return

    df = pd.DataFrame(result["data"])

    display_cols = [
        "site_id",
        "patient_count",
        "total_ae_count",
        "serious_ae_count",
    ]
    display_cols = [col for col in display_cols if col in df.columns]

    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    chart_df = df.set_index("site_id")[["total_ae_count", "serious_ae_count"]]
    st.bar_chart(chart_df)