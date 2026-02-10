from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import duckdb

from app.core.config import settings
from app.infra.fs_lake import lake_root, ensure_lake_dirs


@dataclass(frozen=True)
class ColumnSet:
    has_named_schema: bool
    cols: set[str]

    def pick(self, preferred: Sequence[str], fallback: str) -> str:
        for c in preferred:
            if c in self.cols:
                return c
        return fallback


def _parquet_glob_for_dates(since: str | None, until: str | None) -> str:
    """Return a parquet glob path with basic partition pruning.

    Layout: data_lake/events/dt=YYYY-MM-DD/*.parquet
    - If since==until -> exact partition
    - Else -> broad glob (POC). (vNext: catalog + range pruning)
    """
    root = lake_root()
    base = root / "events"

    if since and until and since == until:
        return str(base / f"dt={since}" / "*.parquet")
    if since and not until:
        # single date partition best-effort (avoid downloading too much)
        return str(base / f"dt={since}" / "*.parquet")
    # broad scan (POC)
    return str(base / "dt=*" / "*.parquet")


def _detect_columns(con: duckdb.DuckDBPyConnection, parquet_glob: str) -> ColumnSet:
    # Use DESCRIBE on read_parquet to get columns without scanning full data
    try:
        df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_glob}') LIMIT 1").fetch_df()
        cols = set(df["column_name"].tolist())
        has_named = "GlobalEventID" in cols and "EventCode" in cols
        return ColumnSet(has_named_schema=has_named, cols=cols)
    except Exception:
        return ColumnSet(has_named_schema=False, cols=set())


def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(settings.duckdb_db_path)


def search_fulltext(query: str, since: str | None, until: str | None, limit: int) -> tuple[int, list[dict]]:
    ensure_lake_dirs()
    parquet_glob = _parquet_glob_for_dates(since, until)
    con = connect()

    sql = f"""
    WITH t AS (SELECT * FROM read_parquet('{parquet_glob}'))
    SELECT *, (concat_ws(' ', *)) AS _all
    FROM t
    WHERE lower((concat_ws(' ', *))) LIKE '%' || lower(?) || '%'
    LIMIT ?
    """
    df = con.execute(sql, [query, limit]).fetch_df()
    count = len(df)
    rows = df.drop(columns=[c for c in df.columns if c == "_all"], errors="ignore").to_dict(orient="records")
    return count, rows


def top_values(
    field_candidates: Sequence[str],
    fallback: str,
    since: str | None,
    until: str | None,
    limit: int,
) -> list[dict]:
    """Generic group-by count over a field (named schema preferred).""
    ensure_lake_dirs()
    parquet_glob = _parquet_glob_for_dates(since, until)
    con = connect()
    cols = _detect_columns(con, parquet_glob)
    field = cols.pick(field_candidates, fallback)

    sql = f"""
    WITH t AS (SELECT * FROM read_parquet('{parquet_glob}'))
    SELECT {field} AS key, COUNT(*) AS n
    FROM t
    WHERE {field} IS NOT NULL AND {field} <> ''
    GROUP BY 1
    ORDER BY n DESC
    LIMIT ?
    """
    df = con.execute(sql, [limit]).fetch_df()
    return df.to_dict(orient="records")


def tone_stats(since: str | None, until: str | None) -> dict:
    """Compute tone statistics if AvgTone exists; else returns empty.""
    ensure_lake_dirs()
    parquet_glob = _parquet_glob_for_dates(since, until)
    con = connect()
    cols = _detect_columns(con, parquet_glob)
    if "AvgTone" not in cols.cols:
        return {"available": False}

    sql = f"""
    WITH t AS (SELECT try_cast(AvgTone AS DOUBLE) AS tone FROM read_parquet('{parquet_glob}'))
    SELECT
      COUNT(*) AS n,
      AVG(tone) AS avg_tone,
      MIN(tone) AS min_tone,
      MAX(tone) AS max_tone
    FROM t
    WHERE tone IS NOT NULL
    """
    row = con.execute(sql).fetchone()
    return {
        "available": True,
        "n": int(row[0]) if row and row[0] is not None else 0,
        "avg_tone": float(row[1]) if row and row[1] is not None else None,
        "min_tone": float(row[2]) if row and row[2] is not None else None,
        "max_tone": float(row[3]) if row and row[3] is not None else None,
    }
