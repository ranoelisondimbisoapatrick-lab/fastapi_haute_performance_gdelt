"""run_scheduler.py

Periodic ingestion runner (no Docker).

Default behavior:
- every 15 minutes
- ingest 1 batch

Config via env:
- INGEST_INTERVAL_MINUTES (default 15)
- INGEST_N_BATCHES (default 1)

Usage:
  poetry run python run_scheduler.py

Notes:
- This is intentionally simple (while-loop + sleep).
- In production you might use APScheduler, Celery beat, Airflow, or Kubernetes CronJobs.
"""

import asyncio
import os
from datetime import datetime
from typing import Final

from app.tasks import run_ingestion_now

DEFAULT_INTERVAL_MIN: Final[int] = 15
DEFAULT_N_BATCHES: Final[int] = 1


def _int_env(name: str, default: int) -> int:
    """Read an int from environment safely."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


async def main() -> None:
    """Main scheduler loop."""
    interval = _int_env("INGEST_INTERVAL_MINUTES", DEFAULT_INTERVAL_MIN)
    n = _int_env("INGEST_N_BATCHES", DEFAULT_N_BATCHES)

    print(f"[scheduler] start | every {interval} min | n_batches={n}")

    while True:
        started = datetime.utcnow()
        print(f"[scheduler] ingest start: {started.isoformat()}Z")

        try:
            res = await run_ingestion_now(n)
            ok = sum(1 for x in res.get("ingested", []) if x.get("status") == "ok")
            total = len(res.get("ingested", []))
            print(f"[scheduler] ingest done: ok={ok}/{total}")
        except Exception as exc:
            # Never stop the loop on a transient failure.
            print(f"[scheduler] ingest failed: {exc}")

        await asyncio.sleep(interval * 60)


if __name__ == "__main__":
    asyncio.run(main())
