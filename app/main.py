from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import metrics_middleware, metrics_endpoint
from app.api.v1.routes import router as v1_router

# Configure logging ONCE at startup
configure_logging()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middlewares
    app.middleware("http")(metrics_middleware)

    # Routes
    app.include_router(v1_router)

    @app.get("/health", tags=["system"])
    async def health():
        return {
            "status": "ok",
            "env": settings.app_env,
        }

    @app.get("/metrics", tags=["system"])
    def metrics():
        return metrics_endpoint()

    return app


# 🔴 POINT D’ENTRÉE FASTAPI
app = create_app()
