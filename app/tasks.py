from __future__ import annotations

"""app.tasks

High-level task orchestration for ingestion.

This module sits above low-level services:
- app.services.gdelt: discovers available batches
- app.services.ingest: downloads + writes Parquet to filesystem lake

Design goals:
- Keep API requests non-blocking (BackgroundTasks in local mode).
- Keep a stable outward contract (`queued` count) across modes.
- Provide structured results to make debugging and observability easier.
"""

import logging
from typing import Any

from app.services.gdelt import fetch_lastupdate, pick_recent
from app.services.ingest import ingest_one

logger = logging.getLogger(__name__)


async def run_ingestion_now(n_batches: int) -> dict[str, Any]:
    """Run ingestion immediately (async).

    Args:
        n_batches: Number of most recent batches to ingest.

    Returns:
        A dict with a stable structure:
        {
          "ingested": [
            {"status": "ok", "path": "...", "dt": "...", "ts": "...", "url": "..."},
            {"status": "failed", "url": "...", "error": "..."},
          ]
        }

    Notes:
        - Errors are captured per batch so one failure doesn't stop others.
        - This function is shared by:
          * API background tasks
          * scheduler (periodic)
          * one-shot CLI runner
    """
    logger.info("Ingestion started (n_batches=%s)", n_batches)

    files = await fetch_lastupdate()
    picked = pick_recent(files, n_batches)

    results: list[dict[str, Any]] = []
    for gf in picked:
        try:
            # Download + convert to Parquet and store in filesystem Data Lake.
            res = await ingest_one(gf)
            results.append({"status": "ok", **res})
        except Exception as exc:
            logger.exception("Ingestion failed for url=%s", gf.url)
            results.append({"status": "failed", "url": gf.url, "error": str(exc)})

    ok = sum(1 for r in results if r.get("status") == "ok")
    logger.info("Ingestion finished (ok=%s/%s)", ok, len(results))

    return {"ingested": results}


async def enqueue_ingestion(n_batches: int) -> int:
    """Queue ingestion.

    Local mode implementation:
    - No external queue/worker is used.
    - FastAPI BackgroundTasks starts `run_ingestion_now` in-process.
    - We return 1 to keep the API contract stable.

    Industrial mode (future):
    - Enqueue a job to Redis/Arq/Celery and return the queued count.
    """
    _ = n_batches  # kept for interface stability
    return 1
