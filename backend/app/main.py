"""
Application factory for Socratica FastAPI backend.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    logger.info(
        "Starting %s (env=%s)",
        settings.app_name,
        settings.app_env,
    )
    # Future: initialise DB connection pool, verify Langflow connectivity, etc.
    yield
    logger.info("Shutting down %s", settings.app_name)
    # Future: close DB connection pool, flush metrics, etc.


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Socratica — AI Teaching Assistant based on RAG. "
            "Grounded Knowledge + Socratic Learning + Human Escalation."
        ),
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        openapi_url="/openapi.json" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    origins = settings.cors_allowed_origins
    if settings.frontend_origin and settings.frontend_origin not in origins:
        origins = [*origins, settings.frontend_origin]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(application)

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(api_router)

    from app.api.v1.endpoints.health import router as health_router
    application.include_router(health_router, prefix="/api", tags=["health"])

    return application


app = create_app()
