import duckdb
from app.core.config import settings


def connect():
    # Local DuckDB file used for caching metadata; queries read Parquet directly from filesystem.
    # In prod, you can point DuckDB to S3 via httpfs extension (or query engine like Trino).
    return duckdb.connect(settings.duckdb_db_path)
