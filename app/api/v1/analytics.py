from __future__ import annotations

from fastapi import APIRouter, Query
from app.services.duckdb_queries import top_values, tone_stats

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/top-event-codes")
def top_event_codes(
    since: str | None = None,
    until: str | None = None,
    limit: int = Query(10, ge=1, le=200),
):
    # Named schema: EventCode; fallback: c27 (approx position in many exports)
    rows = top_values(["EventCode", "EventBaseCode", "EventRootCode"], fallback="c27", since=since, until=until, limit=limit)
    return {"field": "EventCode", "rows": rows}


@router.get("/top-countries")
def top_countries(
    since: str | None = None,
    until: str | None = None,
    limit: int = Query(10, ge=1, le=200),
):
    # Named schema: ActionGeo_CountryCode (or Actor1CountryCode)
    rows = top_values(
        ["ActionGeo_CountryCode", "Actor1CountryCode", "Actor2CountryCode"],
        fallback="c55",
        since=since,
        until=until,
        limit=limit,
    )
    return {"field": "ActionGeo_CountryCode", "rows": rows}


@router.get("/tone")
def tone(
    since: str | None = None,
    until: str | None = None,
):
    return tone_stats(since=since, until=until)
