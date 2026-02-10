"""app.api.v1.routes

Core API v1 routes:
- trigger ingestion (background task in local mode)
- full-text search (DuckDB over Parquet)

OpenAPI/Swagger notes:
- Response models are declared with `response_model=...` for strong schemas.
- Query params are documented with descriptions, constraints and examples.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Query

from app.schemas import IngestTriggerResponse, EventSearchResponse
from app.tasks import enqueue_ingestion, run_ingestion_now
from app.services.query import search_events

router = APIRouter(prefix="/api/v1")


@router.post(
    "/ingest/trigger",
    response_model=IngestTriggerResponse,
    tags=["ingestion"],
    summary="Trigger ingestion of recent GDELT batches",
    description=(
        "Queues an ingestion job and starts ingestion in a background task (local mode). "
        "This keeps the HTTP request fast and non-blocking."
    ),
    responses={
        200: {"description": "Ingestion scheduled successfully."},
        422: {"description": "Validation error (bad parameters)."},
    },
)
async def trigger_ingest(
    background_tasks: BackgroundTasks,
    n_batches: int = Query(
        2,
        ge=1,
        le=20,
        description="Number of most recent batches to ingest (1..20).",
        examples=[1, 2],
    ),
) -> IngestTriggerResponse:
    queued = await enqueue_ingestion(n_batches=n_batches)
    background_tasks.add_task(run_ingestion_now, n_batches)
    return IngestTriggerResponse(queued=queued)


@router.get(
    "/events/search",
    response_model=EventSearchResponse,
    tags=["events"],
    summary="Full-text search in ingested events",
    description=(
        "Runs a DuckDB query over Parquet files stored in the filesystem Data Lake. "
        "Search is implemented with a case-insensitive LIKE over a concatenation of all columns."
    ),
    responses={
        200: {"description": "Search results returned successfully."},
        422: {"description": "Validation error (bad parameters)."},
    },
)
async def events_search(
    query: str = Query(
        ...,
        min_length=2,
        description="Search term (min length 2).",
        examples=["protest", "election", "Madagascar"],
    ),
    since: str | None = Query(
        default=None,
        description="ISO date YYYY-MM-DD. Best-effort partition selection (dt=...).",
        examples=["2026-02-10"],
    ),
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of rows returned (1..500).",
        examples=[20, 50],
    ),
) -> EventSearchResponse:
    count, rows = search_events(query=query, since=since, limit=limit)
    return EventSearchResponse(count=count, rows=rows)
