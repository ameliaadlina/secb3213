"""
Shared response shapes. Every list endpoint must return the envelope
required by the assignment spec:
    { total: int, page: int, limit: int, data: [ ... ] }
"""
from typing import Any, List
from pydantic import BaseModel
from fastapi import Query
from config import DEFAULT_PAGE, DEFAULT_LIMIT, MAX_LIMIT


class Envelope(BaseModel):
    total: int
    page: int
    limit: int
    data: List[Any]


def paginate(cursor, collection, mongo_filter: dict, page: int, limit: int) -> Envelope:
    """
    Shared pagination helper — use this instead of re-writing skip/limit
    math in every router.
    """
    total = collection.count_documents(mongo_filter)
    skip = (page - 1) * limit
    data = list(cursor.skip(skip).limit(limit))
    for doc in data:
        doc["_id"] = str(doc["_id"])
    return Envelope(total=total, page=page, limit=limit, data=data)


def pagination_params(
    page: int = Query(DEFAULT_PAGE, ge=1),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
):
    """Reusable FastAPI dependency: `page` and `limit` query params."""
    return {"page": page, "limit": limit}
