"""
Langflow health check endpoint.

Verifies that the FastAPI backend can reach the Langflow Docker instance.
This endpoint is INTERNAL — intended for ops/monitoring, not for end-users.

Security (docs/ai.md SEC-08):
- On failure, only a safe "unavailable" message is returned to the client.
- Internal error details (connection errors, stack traces) are logged
  server-side only and never forwarded to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.langflow.client import LangflowClient
from app.services.langflow.exceptions import LangflowError

logger = get_logger(__name__)

router = APIRouter()


class ServiceStatusResponse(BaseModel):
    status: str  # "ok" | "unavailable" | "not_configured"
    service: str
    detail: str | None = None  # only populated in non-production for diagnostics


@router.get(
    "/health/langflow",
    response_model=ServiceStatusResponse,
    summary="Langflow connectivity check",
    description=(
        "Checks whether the FastAPI backend can reach the Langflow Docker instance. "
        "Returns 'unavailable' (with HTTP 503) if Langflow cannot be reached. "
        "Does not expose internal error details to the client."
    ),
)
async def langflow_health() -> ServiceStatusResponse:
    """
    Probe the Langflow /health_check endpoint.

    HTTP 200 + status="ok"           → Langflow is reachable and healthy.
    HTTP 503 + status="unavailable"  → Langflow cannot be reached.
    HTTP 503 + status="not_configured" → LANGFLOW_BASE_URL is not set.
    """
    if not settings.langflow_base_url:
        logger.warning("Langflow health check requested but LANGFLOW_BASE_URL is not configured.")
        return ServiceStatusResponse(
            status="not_configured",
            service="langflow",
            detail="LANGFLOW_BASE_URL is not set. Configure it in your .env file."
            if settings.app_debug
            else None,
        )

    try:
        async with LangflowClient() as client:
            health = await client.health_check()
        logger.info("Langflow health check: %s", health.status)
        return ServiceStatusResponse(status="ok", service="langflow")

    except LangflowError as exc:
        # Log the full exception server-side for debugging.
        logger.warning("Langflow health check failed: %s", exc.message)
        return ServiceStatusResponse(
            status="unavailable",
            service="langflow",
            # Only include a diagnostic detail in debug mode to avoid
            # leaking internal topology to clients in production.
            detail=exc.message if settings.app_debug else None,
        )
    except Exception:
        logger.exception("Langflow health check: unexpected error")
        return ServiceStatusResponse(status="unavailable", service="langflow")
