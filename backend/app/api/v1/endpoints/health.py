"""
Health check endpoint.

PRD reference: Section 9.1 (Health & Readiness)
"""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Service health check")
async def health_check() -> dict[str, str]:
    """
    Return basic service health information.

    Does NOT require authentication (PRD F-09.1).
    Used by container orchestrators and load balancers to determine liveness.
    """
    return {"status": "ok", "service": settings.app_name}
