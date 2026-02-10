from __future__ import annotations

"""app.worker

Optional Arq worker entrypoint (Redis-based).

This module is NOT required for the 100% local mode, but it is kept to
demonstrate the POC -> industrial path.

Run:
  poetry run python -m app.worker

Notes:
- Uses Redis as a job queue backend.
- Job functions must be listed in WorkerSettings.functions.
"""

import logging
from typing import Any

from arq import Worker
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging import configure_logging
from app.services.gdelt import fetch_lastupdate, pick_recent
from app.services.ingest import ingest_one

logger = logging.getLogger(__name__)


async def ingest_recent_gdelt(ctx: dict[str, Any], n_batches: int = 2) -> dict[str, Any]:
    """Arq job: ingest recent GDELT batches.

    Args:
        ctx: Arq context dict (unused here but kept for compatibility).
        n_batches: Number of most recent batches to ingest.

    Returns:
        Dict with per-batch status (same structure as local run_ingestion_now).
    """
    _ = ctx
    files = await fetch_lastupdate()
    picked = pick_recent(files, n_batches)

    results: list[dict[str, Any]] = []
    for gf in picked:
        try:
            res = await ingest_one(gf)
            results.append({"status": "ok", **res})
        except Exception as exc:
            logger.exception("Worker ingestion failed for %s", gf.url)
            results.append({"status": "failed", "url": gf.url, "error": str(exc)})
    return {"ingested": results}


class WorkerSettings:
    """Arq settings used by the Worker runtime."""

    functions = [ingest_recent_gdelt]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)


def main() -> None:
    """Start the Arq worker process."""
    configure_logging()
    logger.info("Starting Arq worker (redis=%s:%s)", settings.redis_host, settings.redis_port)
    worker = Worker(WorkerSettings)
    worker.run()


if __name__ == "__main__":
    main()
