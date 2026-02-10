from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import metrics_middleware, metrics_endpoint
from app.api.v1.routes import router as v1_router
from app.api.v1.analytics import router as analytics_router

configure_logging()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.middleware("http")(metrics_middleware)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "env": settings.app_env}

    @app.get("/metrics", tags=["system"])
    def metrics():
        return metrics_endpoint()

    app.include_router(v1_router)
    app.include_router(analytics_router)
    return app


app = create_app()
