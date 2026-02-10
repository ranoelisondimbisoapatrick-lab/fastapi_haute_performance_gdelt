from __future__ import annotations

"""app.infra.fs_lake

Filesystem-based Data Lake helper.

Layout:
  {DATA_LAKE_PATH}/events/dt=YYYY-MM-DD/batch_ts=YYYYMMDDHHMMSS.parquet

Why:
- Mimics the common cloud layout (S3 partitions) while staying 100% local.
- Enables simple partition selection by date (pruning best-effort).

Good practices:
- Keep filesystem paths centralized in one place.
- Ensure directories exist before writing.
"""

from pathlib import Path

from app.core.config import settings


def lake_root() -> Path:
    """Return the root directory of the local Data Lake."""
    return Path(settings.data_lake_path).resolve()


def ensure_lake_dirs() -> None:
    """Create the Data Lake root directory if needed."""
    lake_root().mkdir(parents=True, exist_ok=True)


def parquet_path(dt: str, ts: str) -> Path:
    """Build the output Parquet path for a given partition date and batch timestamp."""
    root = lake_root()
    p = root / "events" / f"dt={dt}" / f"batch_ts={ts}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
