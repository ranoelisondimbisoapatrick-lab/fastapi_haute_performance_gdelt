from __future__ import annotations

from pathlib import Path
from app.core.config import settings


def lake_root() -> Path:
    return Path(settings.data_lake_path).resolve()


def ensure_lake_dirs() -> None:
    root = lake_root()
    root.mkdir(parents=True, exist_ok=True)


def parquet_path(dt: str, ts: str) -> Path:
    # Partition layout: data_lake/events/dt=YYYY-MM-DD/batch_ts=YYYYMMDDHHMMSS.parquet
    root = lake_root()
    p = root / "events" / f"dt={dt}" / f"batch_ts={ts}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
