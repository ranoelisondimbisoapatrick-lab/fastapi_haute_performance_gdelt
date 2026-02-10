"""app.api.v1.analytics

Analytics (OLAP) endpoints built on top of the Parquet filesystem Data Lake using DuckDB.

These endpoints are read-only and designed for quick demonstrations:
- top event codes
- top countries
- tone statistics

OpenAPI/Swagger notes:
- Using `response_model` yields strong schemas in /docs and /openapi.json.
- Parameters are documented via Query constraints and docstrings.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import TopValuesResponse, ToneStatsResponse
from app.services.duckdb_queries import top_values, tone_stats

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get(
    "/top-event-codes",
    response_model=TopValuesResponse,
    summary="Top Event Codes",
    description=(
        "Returns the most frequent event codes from ingested GDELT Events batches. "
        "Prefers the named schema column `EventCode` when available."
    ),
    responses={
        200: {"description": "Top buckets returned successfully."},
    },
)
def top_event_codes(
    since: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
    until: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
    limit: int = Query(10, ge=1, le=200, description="Number of buckets to return."),
) -> dict:
    rows = top_values(
        field_candidates=["EventCode", "EventBaseCode", "EventRootCode"],
        fallback="c27",
        since=since,
        until=until,
        limit=limit,
    )
    return {"field": "EventCode", "rows": rows}


@router.get(
    "/top-countries",
    response_model=TopValuesResponse,
    summary="Top Countries",
    description=(
        "Returns the most frequent country codes based on `ActionGeo_CountryCode` when available. "
        "Falls back to actor country columns if needed."
    ),
    responses={
        200: {"description": "Top buckets returned successfully."},
    },
)
def top_countries(
    since: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
    until: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
    limit: int = Query(10, ge=1, le=200, description="Number of buckets to return."),
) -> dict:
    rows = top_values(
        field_candidates=["ActionGeo_CountryCode", "Actor1CountryCode", "Actor2CountryCode"],
        fallback="c55",
        since=since,
        until=until,
        limit=limit,
    )
    return {"field": "ActionGeo_CountryCode", "rows": rows}


@router.get(
    "/tone",
    response_model=ToneStatsResponse,
    summary="Tone statistics",
    description=(
        "Computes tone stats from `AvgTone` if the column exists in ingested Parquet schema. "
        "Returns `available=false` otherwise."
    ),
    responses={
        200: {"description": "Tone statistics computed (or unavailable)."},
    },
)
def tone(
    since: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
    until: str | None = Query(default=None, description="ISO date YYYY-MM-DD (partition dt=...)."),
) -> dict:
    return tone_stats(since=since, until=until)
