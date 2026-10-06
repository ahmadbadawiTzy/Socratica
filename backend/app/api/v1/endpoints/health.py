"""
Health check endpoint.

PRD F-09.1 — health check is the ONLY endpoint exempt from authentication.
Returns actual service health status for FastAPI, Langflow, and Gemini.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.health_monitor import health_monitor

router = APIRouter()


class ServiceComponentStatus(BaseModel):
    status: str


class ServiceHealthError(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    langflow: ServiceComponentStatus
    gemini: ServiceComponentStatus
    error: ServiceHealthError | None = None


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns actual service health status. "
        "This endpoint is public and does not require authentication."
    ),
)
async def health_check(probe: bool = Query(default=False)) -> HealthResponse:
    report = await health_monitor.check_health(force_probe=probe)
    return HealthResponse(**report)
