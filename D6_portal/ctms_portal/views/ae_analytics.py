"""
Owner: Member C — Adverse Events
Streamlit portal page for AR4, AR5, AR7, and AR10.
"""

import pandas as pd
import streamlit as st

from api_client import api_get


def clean_params(params: dict) -> dict:
    cleaned = {}

    for key, value in params.items():
        if value is None:
            continue

        if value == "":
            continue

        if value == "Any":
            continue

        cleaned[key] = value

    return cleaned


def show_envelope_table(result: dict | None):
    if not result:
        return

    data = result.get("data", [])

    st.caption(
        f"Total results: {result.get('total', 0)} | "
        f"Page: {result.get('page', 1)} | "
        f"Limit: {result.get('limit', 20)}"
    )

    if not data:
        st.info("No data found.")
        return

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


def render():
    st.title("Adverse Events Analytics")

    st.write(
        "This page covers Member C features: patient adverse events, "
        "summary by intervention type, causality-severity matrix, and monthly AE trend."
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "AR4 Patient AEs",
            "AR5 Summary by Type",
            "AR7 Causality Matrix",
            "AR10 Monthly Trend",
        ]
    )

    # ------------------------------------------------------------------
    # AR4 — Retrieve all adverse events for a patient
    # ------------------------------------------------------------------
    with tab1:
        st.subheader("AR4 — Retrieve adverse events for a patient")

        patient_id = st.text_input("Patient ID", value="PT-000001")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            ctcae_grade = st.selectbox(
                "CTCAE Grade",
                ["Any", 1, 2, 3, 4, 5],
            )

        with col2:
            serious_choice = st.selectbox(
                "Serious",
                ["Any", "True", "False"],
            )

        with col3:
            outcome = st.selectbox(
                "Outcome",
                ["Any", "Resolved", "Resolving", "Not resolved", "Fatal", "Unknown"],
            )

        with col4:
            causality = st.selectbox(
                "Causality",
                ["Any", "Unrelated", "Unlikely", "Possible", "Probable", "Definite"],
            )

        if st.button("Search Patient AEs", key="search_patient_ae"):
            serious = None

            if serious_choice == "True":
                serious = True
            elif serious_choice == "False":
                serious = False

            params = clean_params(
                {
                    "ctcae_grade": ctcae_grade,
                    "serious": serious,
                    "outcome": outcome,
                    "causality": causality,
                    "page": 1,
                    "limit": 50,
                }
            )

            result = api_get(
                f"/api/patients/{patient_id}/adverse-events",
                params=params,
            )

            show_envelope_table(result)

    # ------------------------------------------------------------------
    # AR5 — AE summary grouped by intervention type
    # ------------------------------------------------------------------
    with tab2:
        st.subheader("AR5 — AE summary grouped by intervention type")

        trial_id = st.text_input(
            "Optional Trial ID",
            value="",
            placeholder="Example: NCT-20240005",
            key="trial_id_summary",
        )

        if st.button("Load Summary by Intervention Type", key="load_summary_type"):
            params = clean_params(
                {
                    "trial_id": trial_id,
                    "page": 1,
                    "limit": 50,
                }
            )

            result = api_get(
                "/api/adverse-events/summary-by-intervention-type",
                params=params,
            )

            show_envelope_table(result)

            if result and result.get("data"):
                df = pd.DataFrame(result["data"])

                if "intervention_type" in df.columns and "total_ae" in df.columns:
                    chart_df = df.set_index("intervention_type")[["total_ae"]]
                    st.bar_chart(chart_df)

    # ------------------------------------------------------------------
    # AR7 — AE causality-severity matrix for a trial
    # ------------------------------------------------------------------
    with tab3:
        st.subheader("AR7 — AE causality-severity matrix for a trial")

        trial_id_matrix = st.text_input(
            "Trial ID",
            value="NCT-20240005",
            key="trial_id_matrix",
        )

        if st.button("Generate Causality Matrix", key="generate_matrix"):
            result = api_get(
                f"/api/trials/{trial_id_matrix}/adverse-events/causality-matrix",
                params={
                    "page": 1,
                    "limit": 20,
                },
            )

            show_envelope_table(result)

            if result and result.get("data"):
                df = pd.DataFrame(result["data"])

                grade_columns = [
                    "grade_1",
                    "grade_2",
                    "grade_3",
                    "grade_4",
                    "grade_5",
                ]

                if "causality" in df.columns:
                    st.write("Causality-Severity Matrix")

                    matrix_df = df.set_index("causality")

                    existing_grade_columns = [
                        col for col in grade_columns if col in matrix_df.columns
                    ]

                    if existing_grade_columns:
                        st.dataframe(
                            matrix_df[existing_grade_columns],
                            use_container_width=True,
                        )

    # ------------------------------------------------------------------
    # AR10 — Monthly AE trend over time
    # ------------------------------------------------------------------
    with tab4:
        st.subheader("AR10 — Monthly AE trend over time")

        col1, col2 = st.columns(2)

        with col1:
            trial_id_trend = st.text_input(
                "Optional Trial ID",
                value="",
                placeholder="Example: NCT-20240005",
                key="trial_id_trend",
            )

        with col2:
            intervention_type = st.selectbox(
                "Optional Intervention Type",
                [
                    "Any",
                    "Drug",
                    "Biologic",
                    "Device",
                    "Procedure",
                    "Dietary Supplement",
                    "Placebo",
                    "Other",
                ],
            )

        if st.button("Load Monthly AE Trend", key="load_monthly_trend"):
            params = clean_params(
                {
                    "trial_id": trial_id_trend,
                    "intervention_type": intervention_type,
                    "page": 1,
                    "limit": 100,
                }
            )

            result = api_get(
                "/api/adverse-events/monthly-trend",
                params=params,
            )

            show_envelope_table(result)

            if result and result.get("data"):
                df = pd.DataFrame(result["data"])

                if {"year", "month", "ae_count"}.issubset(df.columns):
                    df["month_label"] = (
                        df["year"].astype(str)
                        + "-"
                        + df["month"].astype(str).str.zfill(2)
                    )

                    chart_df = df.set_index("month_label")[["ae_count"]]
                    st.line_chart(chart_df)

                if {"year", "month", "serious_ae_count"}.issubset(df.columns):
                    st.write("Serious AE Trend")

                    df["month_label"] = (
                        df["year"].astype(str)
                        + "-"
                        + df["month"].astype(str).str.zfill(2)
                    )

                    serious_chart_df = df.set_index("month_label")[["serious_ae_count"]]
                    st.line_chart(serious_chart_df)