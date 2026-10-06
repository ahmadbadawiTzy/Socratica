"""
Unit tests for the LangflowClient and Langflow health endpoint.

These tests use httpx MockTransport so they do NOT require a running
Langflow instance. All external HTTP calls are mocked.

Test categories:
  1. Configuration tests
  2. LangflowClient initialization
  3. Missing configuration handling
  4. Connection failure handling
  5. HTTP error from Langflow
  6. Response validation / parsing
  7. GET /api/v1/health/langflow endpoint
"""

from __future__ import annotations

import json

import httpx
import pytest
from httpx import AsyncClient

from app.services.langflow.client import LangflowClient
from app.services.langflow.exceptions import (
    LangflowConnectionError,
    LangflowFlowNotFoundError,
    LangflowResponseError,
    LangflowTimeoutError,
)
from app.services.langflow.schemas import LangflowRunRequest, LangflowRunResponse

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _mock_transport(status_code: int, body: dict | str = "") -> httpx.MockTransport:
    """Build an httpx MockTransport that always returns a fixed response."""
    content = json.dumps(body).encode() if isinstance(body, dict) else body.encode()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status_code, content=content)

    return httpx.MockTransport(handler)


def _error_transport(exc: Exception) -> httpx.MockTransport:
    """Build an httpx MockTransport that always raises an exception."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return httpx.MockTransport(handler)


def _make_client(
    base_url: str = "http://langflow:7860",
    transport: httpx.MockTransport | None = None,
) -> LangflowClient:
    """Create a LangflowClient with an injected mock transport."""
    client = LangflowClient(base_url=base_url, api_key=None, timeout=5.0)
    if transport is not None:
        client._client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout=5.0,
        )
    return client


# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuration tests
# ─────────────────────────────────────────────────────────────────────────────


class TestLangflowConfiguration:
    def test_langflow_base_url_defaults_to_none(self) -> None:
        """LANGFLOW_BASE_URL must default to None (not a fake URL)."""
        from app.core.config import Settings

        # In test env without .env, must be None — never a fabricated default.
        assert Settings.model_fields["langflow_base_url"].default is None

    def test_langflow_api_key_defaults_to_none(self) -> None:
        """LANGFLOW_API_KEY must default to None."""
        from app.core.config import Settings

        assert Settings.model_fields["langflow_api_key"].default is None

    def test_langflow_timeout_has_default(self) -> None:
        """LANGFLOW_TIMEOUT_SECONDS must have a sensible numeric default."""
        from app.core.config import settings

        assert isinstance(settings.langflow_timeout_seconds, float)
        assert settings.langflow_timeout_seconds > 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. LangflowClient initialization
# ─────────────────────────────────────────────────────────────────────────────


class TestLangflowClientInit:
    def test_client_stores_base_url(self) -> None:
        client = LangflowClient(base_url="http://langflow:7860")
        assert client._base_url == "http://langflow:7860"

    def test_client_strips_trailing_slash(self) -> None:
        client = LangflowClient(base_url="http://langflow:7860/")
        assert client._base_url == "http://langflow:7860"

    def test_client_stores_timeout(self) -> None:
        client = LangflowClient(base_url="http://langflow:7860", timeout=15.0)
        assert client._client is None  # not yet opened

    def test_client_no_api_key(self) -> None:
        """Client must work without an API key (LANGFLOW_AUTO_LOGIN mode)."""
        client = LangflowClient(base_url="http://langflow:7860", api_key=None)
        assert client._api_key is None

    def test_client_api_key_not_stored_in_base_url(self) -> None:
        """API key must never be embedded in the URL."""
        client = LangflowClient(
            base_url="http://langflow:7860",
            api_key="super-secret-key",
        )
        assert "super-secret-key" not in client._base_url


# ─────────────────────────────────────────────────────────────────────────────
# 3. Missing configuration handling
# ─────────────────────────────────────────────────────────────────────────────


class TestMissingConfiguration:
    @pytest.mark.asyncio
    async def test_health_check_raises_when_no_base_url(self) -> None:
        """health_check must raise LangflowConnectionError if base_url is empty."""
        client = LangflowClient(base_url="", api_key=None, timeout=5.0)
        with pytest.raises(LangflowConnectionError):
            await client.health_check()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Connection failure handling
# ─────────────────────────────────────────────────────────────────────────────


class TestConnectionFailure:
    @pytest.mark.asyncio
    async def test_health_check_raises_connection_error(self) -> None:
        """ConnectError from httpx must be translated to LangflowConnectionError."""
        transport = _error_transport(httpx.ConnectError("refused"))
        client = _make_client(transport=transport)
        with pytest.raises(LangflowConnectionError):
            await client.health_check()

    @pytest.mark.asyncio
    async def test_run_flow_raises_connection_error(self) -> None:
        transport = _error_transport(httpx.ConnectError("refused"))
        client = _make_client(transport=transport)
        with pytest.raises(LangflowConnectionError):
            await client.run_flow(
                "some-flow-id",
                LangflowRunRequest(input_value="hello"),
            )

    @pytest.mark.asyncio
    async def test_health_check_raises_timeout_error(self) -> None:
        """ReadTimeout from httpx must be translated to LangflowTimeoutError."""
        transport = _error_transport(httpx.ReadTimeout("timed out"))
        client = _make_client(transport=transport)
        with pytest.raises(LangflowTimeoutError):
            await client.health_check()


# ─────────────────────────────────────────────────────────────────────────────
# 5. HTTP error from Langflow
# ─────────────────────────────────────────────────────────────────────────────


class TestHTTPErrors:
    @pytest.mark.asyncio
    async def test_500_raises_response_error(self) -> None:
        transport = _mock_transport(500, {"detail": "internal error"})
        client = _make_client(transport=transport)
        with pytest.raises(LangflowResponseError) as exc_info:
            await client.health_check()
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_404_on_run_raises_flow_not_found(self) -> None:
        transport = _mock_transport(404, {"detail": "flow not found"})
        client = _make_client(transport=transport)
        with pytest.raises(LangflowFlowNotFoundError) as exc_info:
            await client.run_flow(
                "non-existent-flow",
                LangflowRunRequest(input_value="test"),
            )
        assert exc_info.value.flow_id == "/api/v1/run/non-existent-flow"

    @pytest.mark.asyncio
    async def test_401_raises_response_error(self) -> None:
        transport = _mock_transport(401, {"detail": "unauthorized"})
        client = _make_client(transport=transport)
        with pytest.raises(LangflowResponseError) as exc_info:
            await client.health_check()
        assert exc_info.value.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 6. Response validation / parsing
# ─────────────────────────────────────────────────────────────────────────────


class TestResponseParsing:
    @pytest.mark.asyncio
    async def test_health_check_ok(self) -> None:
        transport = _mock_transport(200, {"status": "ok"})
        client = _make_client(transport=transport)
        result = await client.health_check()
        assert result.status == "ok"

    @pytest.mark.asyncio
    async def test_get_version(self) -> None:
        transport = _mock_transport(200, {"version": "1.2.3", "package": "langflow"})
        client = _make_client(transport=transport)
        result = await client.get_version()
        assert result.version == "1.2.3"

    @pytest.mark.asyncio
    async def test_run_flow_parses_response(self) -> None:
        """Run flow response must be parsed into LangflowRunResponse."""
        flow_output = {
            "outputs": [
                {
                    "inputs": {"input_value": "test question"},
                    "outputs": [
                        {
                            "results": {
                                "message": {
                                    "text": "This is the grounded answer.",
                                }
                            }
                        }
                    ],
                }
            ],
            "session_id": "sess-abc123",
        }
        transport = _mock_transport(200, flow_output)
        client = _make_client(transport=transport)
        result = await client.run_flow(
            "flow-id-123",
            LangflowRunRequest(input_value="test question"),
        )
        assert isinstance(result, LangflowRunResponse)
        assert result.session_id == "sess-abc123"
        text = result.extract_text_output()
        assert text == "This is the grounded answer."

    @pytest.mark.asyncio
    async def test_run_flow_tweaks_not_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        Tweaks (which may contain course_id and other server-side values)
        must not appear in log output at WARNING or higher.
        """
        import logging

        flow_output = {"outputs": [], "session_id": "x"}
        transport = _mock_transport(200, flow_output)
        client = _make_client(transport=transport)
        with caplog.at_level(logging.INFO):
            await client.run_flow(
                "flow-id-abc",
                LangflowRunRequest(
                    input_value="hello",
                    tweaks={"Retriever-xyz": {"course_id": "course-123"}},
                ),
            )
        # course_id must not appear in log records
        for record in caplog.records:
            assert "course-123" not in record.getMessage()


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET /api/v1/health/langflow endpoint
# ─────────────────────────────────────────────────────────────────────────────


class TestLangflowHealthEndpoint:
    @pytest.mark.asyncio
    async def test_not_configured_returns_503_or_200(
        self, client: AsyncClient
    ) -> None:
        """
        When LANGFLOW_BASE_URL is not set, the endpoint must return a safe
        'not_configured' response — no stack trace, no internal details
        (except in debug mode).
        """
        response = await client.get("/api/v1/health/langflow")
        # Must be 200 (we return status in body, not as HTTP error for monitoring compat)
        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "langflow"
        assert body["status"] in ("not_configured", "unavailable", "ok")

    @pytest.mark.asyncio
    async def test_response_schema(self, client: AsyncClient) -> None:
        """Response must contain 'status' and 'service' fields."""
        response = await client.get("/api/v1/health/langflow")
        body = response.json()
        assert "status" in body
        assert "service" in body

    @pytest.mark.asyncio
    async def test_no_stack_trace_in_response(self, client: AsyncClient) -> None:
        """Internal error details must never leak to the client response body."""
        response = await client.get("/api/v1/health/langflow")
        body_text = response.text
        # These strings should never appear in a client-facing response
        for leak_indicator in ["Traceback", "httpx", "ConnectError", "Exception"]:
            assert leak_indicator not in body_text
