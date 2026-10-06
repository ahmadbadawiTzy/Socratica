"""
Tests for GET /api/v1/health endpoint.

PRD F-09.1 — health check must NOT require authentication.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_schema(client: AsyncClient) -> None:
    """Health response must contain 'status' and 'service' fields."""
    response = await client.get("/api/v1/health")
    body = response.json()
    assert body["status"] in ("connected", "ok", "degraded", "service_error", "not_connected")
    assert "service" in body
    assert "langflow" in body
    assert "gemini" in body
    assert isinstance(body["service"], str)
    assert body["service"] != ""


@pytest.mark.asyncio
async def test_health_service_name(client: AsyncClient) -> None:
    """Service name in health response must match application config."""
    from app.core.config import settings

    response = await client.get("/api/v1/health")
    body = response.json()
    assert body["service"] == settings.app_name


@pytest.mark.asyncio
async def test_health_no_authentication_required(client: AsyncClient) -> None:
    """
    Health endpoint must be accessible without any Authorization header.
    This is a security baseline: the endpoint is explicitly exempted from auth
    (PRD F-09.1). All other endpoints will require auth in Phase 2.
    """
    response = await client.get("/api/v1/health")
    # Must NOT return 401 or 403
    assert response.status_code not in (401, 403)
