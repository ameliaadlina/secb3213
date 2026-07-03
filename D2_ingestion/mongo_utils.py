"""Shared MongoDB collection setup, used by all four ingest_*.py scripts."""
import json
import os

from pymongo.errors import CollectionInvalid


def get_validator(schema_dir: str, filename: str) -> dict:
    with open(os.path.join(schema_dir, filename)) as f:
        return json.load(f)


def ensure_collection(db, name: str, validator: dict):
    """(Re)create a collection with its D1 schema validator attached."""
    if name in db.list_collection_names():
        db.drop_collection(name)
    try:
        db.create_collection(name, validator=validator)
    except CollectionInvalid:
        pass
    except NotImplementedError:
        # Environments that don't support the validator option (e.g. some
        # test doubles) — fall back to a plain collection instead of
        # failing ingestion entirely.
        print(f"Warning: validator not supported here, creating '{name}' without it.")
        db.create_collection(name)


def print_samples(db, name: str, n: int = 3):
    print(f"\nSample documents from '{name}':")
    for doc in db[name].find().limit(n):
        doc["_id"] = str(doc["_id"])
        print(json.dumps(doc, indent=2, default=str))
        print("-" * 60)
