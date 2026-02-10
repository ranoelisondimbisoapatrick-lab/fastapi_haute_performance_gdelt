from __future__ import annotations

from app.core.config import settings
from app.services.gdelt import fetch_lastupdate, pick_recent
from app.services.ingest import ingest_one


async def run_ingestion_now(n_batches: int) -> dict:
    files = await fetch_lastupdate()
    picked = pick_recent(files, n_batches)
    results = []
    for gf in picked:
        try:
            res = await ingest_one(gf)
            results.append({"status": "ok", **res})
        except Exception as e:
            results.append({"status": "failed", "url": gf.url, "error": str(e)})
    return {"ingested": results}


async def enqueue_ingestion(n_batches: int) -> int:
    """Local mode: ingestion is triggered directly from the API background task."""
    # Keep same API contract: return number of queued jobs
    return 1
