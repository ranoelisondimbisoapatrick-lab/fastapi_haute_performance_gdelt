from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_name: str = "fastapi-gdelt-industrial"
    local_mode: bool = True
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "app"
    postgres_user: str = "app"
    postgres_password: str = "app"

    redis_host: str = "localhost"
    redis_port: int = 6379

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "gdelt-lake"

    gdelt_lastupdate_url: str = "https://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    gdelt_max_download_mb: int = 200

    duckdb_db_path: str = "/tmp/analytics.duckdb"

    # Local filesystem Data Lake (Parquet)
    data_lake_path: str = "./data_lake"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
