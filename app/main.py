from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import metrics_middleware, metrics_endpoint
from app.api.v1.routes import router as v1_router

configure_logging()

app = FastAPI(title=settings.app_name)

app.middleware("http")(metrics_middleware)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/metrics")
def metrics():
    return metrics_endpoint()


app.include_router(v1_router)
