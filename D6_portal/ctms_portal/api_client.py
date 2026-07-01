"""
Shared helper for calling the CTMS API from the portal. Every page should
go through here rather than calling `requests.get` directly — keeps error
handling and the response-envelope unwrapping in one place.
"""
import requests
import streamlit as st
from config import API_BASE_URL


def api_get(path: str, params: dict | None = None) -> dict | None:
    """
    GET a JSON endpoint from the CTMS API. Returns the parsed response
    (the full envelope: {total, page, limit, data}) or None on error,
    after showing a st.error() message.
    """
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        st.error(f"Could not reach the API at {API_BASE_URL}. Is uvicorn running?")
        return None

    if resp.status_code == 404:
        st.warning("No results found for this query.")
        return None
    if resp.status_code == 422:
        st.error(f"Invalid parameters: {resp.json().get('detail')}")
        return None
    if resp.status_code >= 500:
        st.error(f"API error: {resp.json().get('detail', 'unknown error')}")
        return None

    resp.raise_for_status()
    return resp.json()
