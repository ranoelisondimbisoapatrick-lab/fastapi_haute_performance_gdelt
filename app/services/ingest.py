from __future__ import annotations

"""app.services.ingest

Ingestion pipeline for a single GDELT batch:
- stream download zip to a temp file (memory efficient)
- extract CSV file (stream copy)
- convert CSV -> Parquet using PyArrow
- write Parquet to filesystem Data Lake (partitioned)

Good practices:
- Safety cap on download size (gdelt_max_download_mb)
- Avoid loading entire zip in memory
- Use compression (ZSTD) to reduce disk footprint
"""

import tempfile
from datetime import datetime
from pathlib import Path

import httpx
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from app.core.config import settings
from app.domain.gdelt_events_schema import EVENTS_COLUMNS
from app.infra.fs_lake import ensure_lake_dirs, parquet_path
from .gdelt import GdeltFile


async def _download_to_file(url: str, dest: Path) -> None:
    """Stream-download a URL into a local file (memory-efficient)."""
    max_bytes = settings.gdelt_max_download_mb * 1024 * 1024
    downloaded = 0

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                async for chunk in r.aiter_bytes():
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        raise RuntimeError(f"Download exceeds limit ({settings.gdelt_max_download_mb} MB).")
                    f.write(chunk)


def _extract_single_member(zip_path: Path, out_dir: Path) -> Path:
    """Extract the first (and usually only) member of a zip to out_dir."""
    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if not names:
            raise RuntimeError("Empty zip")
        name = names[0]
        out = out_dir / name
        out.parent.mkdir(parents=True, exist_ok=True)

        # Stream copy to avoid memory blowups
        with zf.open(name, "r") as src, out.open("wb") as dst:
            while True:
                buf = src.read(1024 * 1024)
                if not buf:
                    break
                dst.write(buf)
        return out


def _write_events_parquet(csv_path: Path, out_parquet: Path) -> None:
    """Read a TAB-delimited CSV export and write it to Parquet (ZSTD)."""
    parse_opts = pacsv.ParseOptions(delimiter="\t", newlines_in_values=False)
    read_opts = pacsv.ReadOptions(autogenerate_column_names=True)
    convert_opts = pacsv.ConvertOptions(strings_can_be_null=True)

    table = pacsv.read_csv(
        str(csv_path),
        read_options=read_opts,
        parse_options=parse_opts,
        convert_options=convert_opts,
    )

    # If the width matches known schema, rename columns to meaningful names.
    if table.num_columns == len(EVENTS_COLUMNS):
        table = table.rename_columns(EVENTS_COLUMNS)
    else:
        # Stable generic naming
        cols = [f"c{i+1}" for i in range(table.num_columns)]
        table = table.rename_columns(cols)

    pq.write_table(table, str(out_parquet), compression="zstd")


async def ingest_one(gf: GdeltFile) -> dict:
    """Download one batch and write to LOCAL filesystem as Parquet.

    Args:
        gf: The GDELT batch file to ingest.

    Returns:
        Dict containing:
        - path: local parquet path
        - dt: partition date (YYYY-MM-DD)
        - ts: batch timestamp (YYYYMMDDHHMMSS)
        - url: source url
    """
    ensure_lake_dirs()

    dt = "unknown"
    if gf.ts != "unknown":
        dt = datetime.strptime(gf.ts, "%Y%m%d%H%M%S").date().isoformat()

    out = parquet_path(dt=dt, ts=gf.ts)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        zip_file = tmpdir / f"gdelt_{gf.ts}.zip"
        await _download_to_file(gf.url, zip_file)
        csv_file = _extract_single_member(zip_file, tmpdir)
        _write_events_parquet(csv_file, out)

    return {"path": str(out), "dt": dt, "ts": gf.ts, "url": gf.url}
