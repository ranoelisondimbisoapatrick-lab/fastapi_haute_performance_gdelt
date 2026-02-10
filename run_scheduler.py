"""Run periodic ingestion locally (no Docker).

- Default: every 15 minutes, ingest 1 batch.
- Config via env:
  - INGEST_INTERVAL_MINUTES (default 15)
  - INGEST_N_BATCHES (default 1)

Usage:
  poetry run python run_scheduler.py
"""

import os
import asyncio
from datetime import datetime

from app.tasks import run_ingestion_now


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


async def main() -> None:
    interval = _int_env("INGEST_INTERVAL_MINUTES", 15)
    n = _int_env("INGEST_N_BATCHES", 1)

    print(f"[scheduler] start | every {interval} min | n_batches={n}")
    while True:
        started = datetime.utcnow()
        print(f"[scheduler] ingest start: {started.isoformat()}Z")
        try:
            res = await run_ingestion_now(n)
            ok = sum(1 for x in res.get("ingested", []) if x.get("status") == "ok")
            print(f"[scheduler] ingest done: ok={ok}/{len(res.get('ingested', []))}")
        except Exception as e:
            print(f"[scheduler] ingest failed: {e}")

        await asyncio.sleep(interval * 60)


if __name__ == "__main__":
    asyncio.run(main())
