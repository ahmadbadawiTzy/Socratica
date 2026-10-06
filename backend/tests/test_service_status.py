"""
Unit tests for Service Health and Error Classification.

Verifies:
1. Langflow + Gemini valid -> connected
2. Langflow dead -> not_connected
3. Langflow timeout -> connection_timeout
4. Gemini credential invalid -> authentication_error
5. Gemini quota/token exhausted -> quota_exceeded
6. Gemini rate limit -> rate_limited
7. Langflow flow error -> service_error
8. Recovery after service returns to normal (no fake recovery)
"""

import pytest
from httpx import AsyncClient, ConnectError, TimeoutException

from app.services.langflow.classifier import (
    ServiceStatus,
    classify_error,
    sanitize_text,
)
from app.services.health_monitor import health_monitor
from app.services.langflow.exceptions import (
    LangflowConnectionError,
    LangflowResponseError,
    LangflowTimeoutError,
)


def test_sanitize_text_strips_api_keys() -> None:
    raw = "Failed with key AIzaSyA12345678901234567890123456789012 and bearer abc.def.ghi"
    sanitized = sanitize_text(raw)
    assert "AIza" not in sanitized
    assert "[REDACTED]" in sanitized


def test_classify_quota_exceeded() -> None:
    # HTTP 429 with RESOURCE_EXHAUSTED / quota message
    c1 = classify_error(
        429,
        "Resource has been exhausted (e.g. check quota). You exceeded your current quota.",
    )
    assert c1.status == ServiceStatus.QUOTA_EXCEEDED
    assert c1.code == "QUOTA_EXCEEDED"
    assert "quota telah habis" in c1.user_message.lower()

    # Generic RESOURCE_EXHAUSTED
    c2 = classify_error(500, "google.api_core.exceptions.ResourceExhausted: 429 Resource has been exhausted")
    assert c2.status == ServiceStatus.QUOTA_EXCEEDED
    assert c2.code == "QUOTA_EXCEEDED"


def test_classify_rate_limited() -> None:
    c = classify_error(
        429,
        "Rate limit exceeded: 15 requests per minute allowed.",
    )
    assert c.status == ServiceStatus.RATE_LIMITED
    assert c.code == "RATE_LIMITED"
    assert "laju permintaan" in c.user_message.lower()


def test_classify_authentication_error() -> None:
    c1 = classify_error(401, "API_KEY_INVALID: API key not valid. Please pass a valid API key.")
    assert c1.status == ServiceStatus.AUTHENTICATION_ERROR
    assert c1.code == "AUTHENTICATION_ERROR"

    c2 = classify_error(403, "The caller does not have permission / PERMISSION_DENIED")
    assert c2.status == ServiceStatus.AUTHENTICATION_ERROR
    assert c2.code == "AUTHENTICATION_ERROR"

    c3 = classify_error(500, "Google API Key is required")
    assert c3.status == ServiceStatus.AUTHENTICATION_ERROR


def test_classify_connection_timeout() -> None:
    c = classify_error(None, "The read operation timed out", exc=TimeoutException("timeout"))
    assert c.status == ServiceStatus.CONNECTION_TIMEOUT
    assert c.code == "CONNECTION_TIMEOUT"


def test_classify_not_connected() -> None:
    c1 = classify_error(None, "Connection refused", exc=ConnectError("Connection refused"))
    assert c1.status == ServiceStatus.NOT_CONNECTED
    assert c1.code == "NOT_CONNECTED"

    c2 = classify_error(503, "Bad Gateway / Service Unavailable")
    assert c2.status == ServiceStatus.NOT_CONNECTED


def test_classify_service_error() -> None:
    c = classify_error(500, "Edge between Read File and Recursive Character Text Splitter has invalid handles")
    assert c.status == ServiceStatus.SERVICE_ERROR
    assert c.code == "SERVICE_ERROR"


@pytest.mark.asyncio
async def test_no_fake_recovery() -> None:
    # 1. Simulate failure in Gemini
    health_monitor.record_failure(
        LangflowResponseError(429, "Resource has been exhausted (quota exceeded)")
    )
    assert health_monitor.gemini_status == ServiceStatus.QUOTA_EXCEEDED

    # 2. Check health without force probe (Langflow ping should NOT fake-recover Gemini)
    report = health_monitor._build_report()
    assert report["gemini"]["status"] == "quota_exceeded"
    assert report["status"] == "degraded"

    # 3. Only true chat success or successful probe recovers Gemini
    health_monitor.record_chat_success()
    report2 = health_monitor._build_report()
    assert report2["gemini"]["status"] == "connected"
    assert report2["status"] == "connected"


@pytest.mark.asyncio
async def test_health_endpoints_return_real_schema(client: AsyncClient) -> None:
    # Both /api/v1/health and /api/health should work
    res1 = await client.get("/api/v1/health")
    assert res1.status_code == 200
    b1 = res1.json()
    assert "status" in b1
    assert "langflow" in b1
    assert "gemini" in b1
    assert b1["service"] == "Socratica"

    res2 = await client.get("/api/health")
    assert res2.status_code == 200
    b2 = res2.json()
    assert b2["service"] == b1["service"]
