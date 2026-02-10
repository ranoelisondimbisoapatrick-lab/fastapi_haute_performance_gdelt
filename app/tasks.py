from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings


async def enqueue_ingestion(n_batches: int) -> int:
    pool = await create_pool(RedisSettings(host=settings.redis_host, port=settings.redis_port))
    await pool.enqueue_job("ingest_recent_gdelt", n_batches)
    return 1
