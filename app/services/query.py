import os
import tempfile
import pandas as pd
import duckdb

from app.core.config import settings
from app.infra.s3 import s3_client, ensure_bucket


def _download_partition_to_local(prefix: str, local_dir: str) -> list[str]:
    """POC simplification: download Parquet objects from S3 prefix to local dir for DuckDB."""
    ensure_bucket()
    s3 = s3_client()

    paginator = s3.get_paginator("list_objects_v2")
    paths = []
    for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".parquet"):
                continue
            local_path = os.path.join(local_dir, os.path.basename(key))
            s3.download_file(settings.s3_bucket, key, local_path)
            paths.append(local_path)
    return paths


def search_events(query: str, since: str | None, limit: int) -> tuple[int, list[dict]]:
    """Search within ingested Parquet batches using DuckDB."""
    with tempfile.TemporaryDirectory() as tmp:
        prefix = "events/"
        if since:
            # Since is date YYYY-MM-DD; we download partitions >= since is complex in S3 w/out catalog.
            # POC: download all and filter in SQL (industrial: use catalog + partitions pruning).
            prefix = "events/"
        files = _download_partition_to_local(prefix, tmp)
        if not files:
            return 0, []

        con = duckdb.connect(settings.duckdb_db_path)
        # Very generic schema; we use c1..cN. We'll search in all columns by concatenation.
        paths_sql = ",".join([f"'{p}'" for p in files])
        sql = f"""
        WITH t AS (
          SELECT * FROM read_parquet([{paths_sql}])
        )
        SELECT *,
               (concat_ws(' ', *)) AS _all
        FROM t
        WHERE lower((concat_ws(' ', *))) LIKE '%' || lower(?) || '%'
        LIMIT ?
        """
        df = con.execute(sql, [query, limit]).fetch_df()
        count = len(df)
        rows = df.drop(columns=[c for c in df.columns if c == "_all"], errors="ignore").to_dict(orient="records")
        return count, rows
