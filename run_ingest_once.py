"""Run a one-shot ingestion locally (no API, no Docker).

Usage:
  poetry run python run_ingest_once.py --n 2
"""

import argparse
import asyncio
from app.tasks import run_ingestion_now

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2)
    return ap.parse_args()

async def main():
    args = parse_args()
    res = await run_ingestion_now(args.n)
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
