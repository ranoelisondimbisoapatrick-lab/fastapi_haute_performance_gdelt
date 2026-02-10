import io
import csv
import zipfile
from datetime import datetime
from typing import AsyncIterator

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.core.config import settings
from app.infra.s3 import s3_client, ensure_bucket
from .gdelt import GdeltFile


async def _download_zip(url: str) -> bytes:
    # Safety: hard limit to avoid accidental huge downloads in local POC.
    max_bytes = settings.gdelt_max_download_mb * 1024 * 1024

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            buf = bytearray()
            async for chunk in r.aiter_bytes():
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    raise RuntimeError(f"Download exceeds limit ({settings.gdelt_max_download_mb} MB).")
            return bytes(buf)


def _csv_from_zip(zip_bytes: bytes) -> io.TextIOBase:
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    # GDELT zip contains one CSV
    name = zf.namelist()[0]
    raw = zf.read(name)
    return io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace")


def _events_to_parquet(csv_file: io.TextIOBase, out_path: str) -> None:
    # GDELT Events CSV is tab-delimited in many exports; handle both.
    sample = csv_file.read(4096)
    csv_file.seek(0)
    delimiter = "\t" if "\t" in sample else ","

    reader = csv.reader(csv_file, delimiter=delimiter)
    rows = list(reader)

    if not rows:
        raise RuntimeError("Empty CSV")

    # GDELT exports may not include header; store as generic columns c1..cN
    width = max(len(r) for r in rows)
    cols = [f"c{i+1}" for i in range(width)]
    norm = [r + [""] * (width - len(r)) for r in rows]

    df = pd.DataFrame(norm, columns=cols)

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, out_path, compression="zstd")


async def ingest_one(gf: GdeltFile) -> dict:
    """Download one batch and write to S3 as Parquet, partitioned by date."""
    ensure_bucket()
    s3 = s3_client()

    zip_bytes = await _download_zip(gf.url)
    csv_fp = _csv_from_zip(zip_bytes)

    # Partition: dt=YYYY-MM-DD from gf.ts
    dt = "unknown"
    if gf.ts != "unknown":
        dt = datetime.strptime(gf.ts, "%Y%m%d%H%M%S").date().isoformat()

    local_tmp = f"/tmp/gdelt_{gf.ts}.parquet"
    _events_to_parquet(csv_fp, local_tmp)

    key = f"events/dt={dt}/batch_ts={gf.ts}.parquet"
    with open(local_tmp, "rb") as f:
        s3.upload_fileobj(f, settings.s3_bucket, key)

    return {"s3_key": key, "dt": dt, "ts": gf.ts, "url": gf.url}
