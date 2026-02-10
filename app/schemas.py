from __future__ import annotations

"""app.schemas

Pydantic models used by the FastAPI layer.

Why it matters (OpenAPI/Swagger):
- Declaring `response_model=...` yields strong OpenAPI schemas.
- Field metadata (description, examples) improves Swagger UX.

Good practices applied:
- Stable response contracts (avoid breaking clients).
- Small focused models (one endpoint family = one model family).
- Descriptive Field docs + examples.
"""

from pydantic import BaseModel, Field


class IngestTriggerResponse(BaseModel):
    """Response model for ingestion trigger endpoints.

    The `queued` value stays stable across deployment modes:
    - Local mode (BackgroundTasks): returns 1 (one logical job)
    - Worker/queue mode (Redis/Arq): returns number of jobs queued
    """

    queued: int = Field(
        ...,
        description="Number of jobs queued (contract kept stable across modes).",
        examples=[1],
    )


class EventSearchResponse(BaseModel):
    """Response model for full-text search endpoints."""

    count: int = Field(
        ...,
        description="Number of rows returned in `rows`.",
        examples=[20],
    )
    rows: list[dict] = Field(
        default_factory=list,
        description=(
            "Rows returned by DuckDB. Each row is a dict keyed by Parquet column names. "
            "Schema may be named (GDELT columns) or generic (c1..cN) depending on ingestion."
        ),
        examples=[[{"GlobalEventID": "123", "EventCode": "145"}]],
    )


class TopValueRow(BaseModel):
    """One bucket in a top-values aggregation."""

    key: str = Field(
        ...,
        description="Group key (e.g., event code, country code).",
        examples=["US"],
    )
    n: int = Field(
        ...,
        description="Occurrences for the bucket.",
        examples=[1234],
    )


class TopValuesResponse(BaseModel):
    """Response model for top-values endpoints (GROUP BY COUNT)."""

    field: str = Field(
        ...,
        description="Logical field name used by the endpoint.",
        examples=["EventCode"],
    )
    rows: list[TopValueRow] = Field(
        default_factory=list,
        description="Top buckets ordered by count desc.",
    )


class ToneStatsResponse(BaseModel):
    """Tone statistics output when AvgTone exists in ingested data.

    If AvgTone is not present in the ingested Parquet schema,
    the API returns: {"available": False}
    """

    available: bool = Field(
        ...,
        description="False if AvgTone is not available in the Parquet schema.",
        examples=[True],
    )
    n: int | None = Field(
        None,
        description="Number of rows included in the computation.",
        examples=[100000],
    )
    avg_tone: float | None = Field(
        None,
        description="Average tone.",
        examples=[-0.12],
    )
    min_tone: float | None = Field(
        None,
        description="Minimum tone.",
        examples=[-9.5],
    )
    max_tone: float | None = Field(
        None,
        description="Maximum tone.",
        examples=[8.1],
    )
