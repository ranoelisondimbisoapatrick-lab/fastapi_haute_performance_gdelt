from __future__ import annotations

"""app.services.duckdb_queries

DuckDB query helpers used by the API layer.

Key points:
- Reads Parquet from filesystem Data Lake (partitioned by dt=YYYY-MM-DD).
- Normalizes Windows paths into POSIX-style paths for DuckDB.
- Provides:
  * full-text search (LIKE over concatenated columns)
  * top-values aggregations (GROUP BY)
  * tone statistics (AvgTone) when available

Good practices:
- Keep SQL inside triple-quoted strings.
- Parametrize values (avoid string concatenation for user inputs).
"""

from dataclasses import dataclass
from typing import Sequence

import duckdb

from app.core.config import settings
from app.infra.fs_lake import lake_root, ensure_lake_dirs


@dataclass(frozen=True)
class ColumnSet:
    """Represents detected Parquet columns."""

    has_named_schema: bool
    cols: set[str]

    def pick(self, preferred: Sequence[str], fallback: str) -> str:
        """Pick the first column present in preferred list, else fallback."""
        for c in preferred:
            if c in self.cols:
                return c
        return fallback


def connect() -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection (file-based)."""
    return duckdb.connect(settings.duckdb_db_path)


def _normalize_path_for_duckdb(path: str) -> str:
    """DuckDB path handling prefers forward slashes on Windows."""
    return path.replace("\\", "/")


def _parquet_glob_for_dates(since: str | None, until: str | None) -> str:
    """Return a parquet glob path with best-effort partition pruning.

    Layout: data_lake/events/dt=YYYY-MM-DD/*.parquet

    Strategy (POC):
    - if since==until: scan exactly that partition
    - if since only: scan that partition
    - else: scan all partitions

    Production version would implement a catalog + true pruning for ranges.
    """
    root = lake_root()
    base = root / "events"

    if since and until and since == until:
        return _normalize_path_for_duckdb(str(base / f"dt={since}" / "*.parquet"))
    if since and not until:
        return _normalize_path_for_duckdb(str(base / f"dt={since}" / "*.parquet"))

    return _normalize_path_for_duckdb(str(base / "dt=*" / "*.parquet"))


def _detect_columns(con: duckdb.DuckDBPyConnection, parquet_glob: str) -> ColumnSet:
    """Detect columns with DESCRIBE without scanning the whole dataset."""
    try:
        df = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet_glob}') LIMIT 1"
        ).fetch_df()
        cols = set(df["column_name"].tolist())
        has_named = "GlobalEventID" in cols and "EventCode" in cols
        return ColumnSet(has_named_schema=has_named, cols=cols)
    except Exception:
        return ColumnSet(has_named_schema=False, cols=set())


def search_fulltext(query: str, since: str | None, until: str | None, limit: int) -> tuple[int, list[dict]]:
    """Full-text LIKE search over all columns.

    Implementation detail:
    - DuckDB `concat_ws(' ', *)` concatenates all columns into one string.
    - We then apply a case-insensitive LIKE.

    Args:
        query: search term (user input)
        since/until: best-effort partition selection
        limit: maximum number of rows

    Returns:
        (count, rows) where rows is a list of dicts.
    """
    ensure_lake_dirs()
    parquet_glob = _parquet_glob_for_dates(since, until)
    con = connect()

    sql = f"""
    WITH t AS (SELECT * FROM read_parquet('{parquet_glob}'))
    SELECT *, concat_ws(' ', *) AS _all
    FROM t
    WHERE lower(concat_ws(' ', *)) LIKE '%' || lower(?) || '%'
    LIMIT ?
    """

    df = con.execute(sql, [query, limit]).fetch_df()
    count = len(df)
    rows = df.drop(columns=["_all"], errors="ignore").to_dict(orient="records")
    return count, rows


def top_values(
    field_candidates: Sequence[str],
    fallback: str,
    since: str | None,
    until: str | None,
    limit: int,
) -> list[dict]:
    """Generic GROUP BY COUNT over a selected field.

    - If named schema exists, we prefer semantic columns like EventCode.
    - Otherwise we fall back to a generic column name like c27.

    Returns:
        List[{"key": <value>, "n": <count>}, ...]
    """
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
    """Compute tone statistics from AvgTone when available."""
    ensure_lake_dirs()
    parquet_glob = _parquet_glob_for_dates(since, until)
    con = connect()

    cols = _detect_columns(con, parquet_glob)
    if "AvgTone" not in cols.cols:
        return {"available": False}

    sql = f"""
    WITH t AS (
      SELECT try_cast(AvgTone AS DOUBLE) AS tone
      FROM read_parquet('{parquet_glob}')
    )
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
