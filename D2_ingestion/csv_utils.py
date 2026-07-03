"""
Shared helpers for parsing the raw CSVs in raw_data/ into MongoDB-ready
Python values. All four ingestion scripts use these — keeps the
pipe-delimited-list / date / bool / empty-string conventions consistent.
"""
import csv
from datetime import datetime


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split_pipe(value: str) -> list[str]:
    """'A|B|C' -> ['A', 'B', 'C']. Empty string -> []."""
    if not value or not value.strip():
        return []
    return [v.strip() for v in value.split("|")]


def parse_date(value: str):
    """'2021-08-02' -> datetime(2021, 8, 2). Empty string -> None."""
    if not value or not value.strip():
        return None
    return datetime.strptime(value.strip(), "%Y-%m-%d")


def parse_bool(value: str):
    """'TRUE'/'FALSE' (any case) -> bool. Empty string -> None."""
    if not value or not value.strip():
        return None
    return value.strip().upper() == "TRUE"


def parse_int(value: str):
    if not value or not value.strip():
        return None
    return int(value)


def parse_float(value: str):
    if not value or not value.strip():
        return None
    return float(value)


def none_if_empty(value: str):
    return value.strip() if value and value.strip() else None


def parse_arms(value: str) -> list[dict]:
    """
    'Arm A:Experimental|Arm B:Placebo Comparator' ->
    [{"arm_label": "Arm A", "arm_type": "Experimental", "description": "..."}, ...]

    The source CSV has no free-text arm description column, so one is
    synthesized from the arm_type to satisfy the D1 schema's requirement
    that every arm include a description field.
    """
    arms = []
    for entry in split_pipe(value):
        label, _, arm_type = entry.partition(":")
        label, arm_type = label.strip(), arm_type.strip()
        arms.append({
            "arm_label": label,
            "arm_type": arm_type,
            "description": f"{label} — {arm_type.lower()} treatment group",
        })
    return arms
