import asyncio
import logging
from arq import Worker
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging import configure_logging
from app.services.gdelt import fetch_lastupdate, pick_recent
from app.services.ingest import ingest_one

logger = logging.getLogger("worker")


async def ingest_recent_gdelt(ctx, n_batches: int = 2) -> dict:
    files = await fetch_lastupdate()
    picked = pick_recent(files, n_batches)
    results = []
    for gf in picked:
        try:
            r = await ingest_one(gf)
            results.append({"status": "ok", **r})
        except Exception as e:
            logger.exception("Ingestion failed for %s", gf.url)
            results.append({"status": "failed", "url": gf.url, "error": str(e)})
    return {"ingested": results}


class WorkerSettings:
    functions = [ingest_recent_gdelt]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)


def main() -> None:
    configure_logging()
    logger.info("Starting Arq worker")
    worker = Worker(WorkerSettings)
    worker.run()


if __name__ == "__main__":
    main()
