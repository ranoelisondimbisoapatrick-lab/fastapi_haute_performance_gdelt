"""app.main

FastAPI application entrypoint.

OpenAPI endpoints (default FastAPI behavior):
- Swagger UI: GET /docs
- OpenAPI JSON: GET /openapi.json
- ReDoc: GET /redoc

This project is designed as a POC that can evolve into an industrial backend:
- ingestion of open Big Data (GDELT)
- filesystem Data Lake in Parquet partitions
- analytics using DuckDB
- observability: JSON logs + Prometheus metrics
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import metrics_middleware, metrics_endpoint
from app.api.v1.routes import router as v1_router
from app.api.v1.analytics import router as analytics_router

configure_logging()

TAGS_METADATA = [
    {"name": "system", "description": "System endpoints (health, metrics)."},
    {"name": "ingestion", "description": "Ingestion endpoints (GDELT batches)."},
    {"name": "events", "description": "Event search endpoints (DuckDB over Parquet)."},
    {"name": "analytics", "description": "Analytics endpoints (aggregations)."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "FastAPI haute performance (POC → industriel) : ingestion Big Data open data (GDELT), "
            "Data Lake Parquet (filesystem), analytics DuckDB, métriques Prometheus, logs JSON."
        ),
        contact={"name": "RANOELISON Dimbisoa Adrianno"},
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middlewares
    app.middleware("http")(metrics_middleware)

    # System routes
    @app.get("/health", tags=["system"], summary="Healthcheck")
    async def health():
        """Simple healthcheck endpoint."""
        return {"status": "ok", "env": settings.app_env}

    @app.get("/metrics", tags=["system"], summary="Prometheus metrics")
    def metrics():
        """Prometheus scrape endpoint."""
        return metrics_endpoint()

    # API routers
    app.include_router(v1_router)
    app.include_router(analytics_router)
    return app


# ASGI app for Uvicorn/Gunicorn
app = create_app()
