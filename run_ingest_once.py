"""run_ingest_once.py

One-shot ingestion runner (no API, no Docker).

Usage:
  poetry run python run_ingest_once.py --n 2

Exit codes:
- 0: finished (even if some batches failed; see printed results)
- 1: fatal crash
"""

import argparse
import asyncio
import json
import sys
from typing import Any

from app.tasks import run_ingestion_now


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    ap = argparse.ArgumentParser(description="Run a one-shot GDELT ingestion.")
    ap.add_argument("--n", type=int, default=2, help="Number of batches to ingest (default: 2).")
    return ap.parse_args()


async def main_async(n: int) -> dict[str, Any]:
    """Async entrypoint."""
    return await run_ingestion_now(n)


def main() -> int:
    """CLI main returning an exit code."""
    args = parse_args()
    try:
        res = asyncio.run(main_async(args.n))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"[ingest_once] fatal error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
