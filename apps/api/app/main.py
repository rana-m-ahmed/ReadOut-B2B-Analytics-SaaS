"""FastAPI application bootstrap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_anomalies import router as anomalies_router
from app.api.routes_ask import router as ask_router
from app.api.routes_auth import router as auth_router
from app.api.routes_datasets import router as datasets_router
from app.api.routes_insights import router as insights_router
from app.api.routes_widgets import router as widgets_router
from app.core.config import Settings, get_settings

from app.core.errors import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()

    configure_logging()

    application = FastAPI()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)

    @application.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "environment": resolved_settings.ENVIRONMENT}

    for router in (
        auth_router,
        datasets_router,
        ask_router,
        insights_router,
        anomalies_router,
        widgets_router,
    ):
        application.include_router(router)

    return application


app = create_app()
