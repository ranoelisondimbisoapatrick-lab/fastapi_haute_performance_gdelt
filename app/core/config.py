"""app.core.config

Central configuration using `pydantic-settings`.

Good practices applied:
- Everything configurable via env vars or .env file.
- Safe defaults for local development.
- Keep compatibility fields (Postgres/Redis/S3) to support POC -> industrial evolution.

SSL note (Windows/proxy/AV):
- Some environments may fail HTTPS certificate validation for data.gdeltproject.org.
- Default is HTTP for GDELT_LASTUPDATE_URL to keep the demo runnable.
  You can override via env if HTTPS works for you.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and optional .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "dev"
    app_name: str = "fastapi-gdelt-industrial"
    local_mode: bool = True
    log_level: str = "INFO"

    # Optional: Industrial mode (metadata store)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "app"
    postgres_user: str = "app"
    postgres_password: str = "app"

    # Optional: Industrial mode (job queue)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Optional: legacy S3/MinIO fields kept for compatibility
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "gdelt-lake"

    # GDELT ingestion
    gdelt_lastupdate_url: str = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    gdelt_max_download_mb: int = 200  # safety cap

    # DuckDB (analytics)
    duckdb_db_path: str = "./analytics.duckdb"

    # Local filesystem Data Lake (Parquet)
    data_lake_path: str = "./data_lake"

    @property
    def postgres_dsn(self) -> str:
        """Async DSN for SQLAlchemy (industrial mode)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
