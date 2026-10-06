"""
LangflowClient — HTTP client for communicating with the Langflow Docker instance.

Design principles:
- Base URL and API key are read from environment config; never hardcoded.
- All requests include a configurable timeout (default from settings).
- HTTP errors are translated to domain exceptions (LangflowError subclasses).
- API key is NEVER logged, even at DEBUG level.
- Response bodies are not logged in full to avoid leaking sensitive content.
- course_id injected via tweaks comes from backend authorization, NOT user input.

Langflow Docker setup (ibm-hacktiv8-langflow):
  Container name: langflow
  Host port:      7860
  API key:        not required (LANGFLOW_AUTO_LOGIN=true)
  Base URL:
    - From Socratica backend container (same Docker host, host-network or
      explicit LANGFLOW_BASE_URL env var): http://localhost:7860
    - When both run in the same Docker Compose network:
      use the service name as hostname (e.g. http://langflow:7860)

The correct URL is set via LANGFLOW_BASE_URL in .env — see .env.example.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.langflow.exceptions import (
    LangflowConnectionError,
    LangflowFlowNotFoundError,
    LangflowResponseError,
    LangflowTimeoutError,
)
from app.services.langflow.schemas import (
    LangflowHealthResponse,
    LangflowRunRequest,
    LangflowRunResponse,
    LangflowVersionResponse,
)

logger = get_logger(__name__)


_UNSET = object()


class LangflowClient:
    """
    Async HTTP client for the Langflow REST API.

    Typical usage (as a FastAPI dependency):

        async with LangflowClient() as client:
            health = await client.health_check()
            result  = await client.run_flow(flow_id, request)

    The client can also be used without async context manager if you manage
    the httpx.AsyncClient lifecycle yourself.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None | object = _UNSET,
        timeout: float | None = None,
    ) -> None:
        """
        Initialise the client.

        Args:
            base_url:  Langflow base URL. Defaults to settings.langflow_base_url.
            api_key:   Langflow API key. Defaults to settings.langflow_api_key.
                       Pass None if LANGFLOW_AUTO_LOGIN=true (no auth needed).
            timeout:   Request timeout in seconds. Defaults to
                       settings.langflow_timeout_seconds.
        """
        raw_url = base_url if base_url is not None else (settings.langflow_base_url or "")
        self._base_url: str = raw_url.rstrip("/")
        self._api_key: str | None = api_key if api_key is not _UNSET else settings.langflow_api_key
        self._timeout: float = timeout if timeout is not None else settings.langflow_timeout_seconds
        self._client: httpx.AsyncClient | None = None

        if not self._base_url:
            logger.warning(
                "LANGFLOW_BASE_URL is not configured. "
                "Set it in .env to enable Langflow integration."
            )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def __aenter__(self) -> LangflowClient:
        self._client = self._build_client()
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_client(self) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            # Do NOT log the key value.
            headers["x-api-key"] = self._api_key
            logger.debug("LangflowClient: using API key authentication")
        else:
            logger.debug("LangflowClient: no API key (LANGFLOW_AUTO_LOGIN assumed)")
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=self._timeout,
        )

    def _get_client(self) -> httpx.AsyncClient:
        """Return the active client or create a temporary one."""
        if self._client is not None:
            return self._client
        return self._build_client()

    # ── Request helpers ───────────────────────────────────────────────────────

    async def _get(self, path: str) -> httpx.Response:
        """Perform a GET request with standardised error handling."""
        client = self._get_client()
        try:
            response = await client.get(path)
        except httpx.ConnectError:
            raise LangflowConnectionError(self._base_url) from None
        except httpx.TimeoutException:
            raise LangflowTimeoutError(self._timeout) from None
        except httpx.RequestError as exc:
            raise LangflowConnectionError(self._base_url) from exc
        self._raise_for_status(response, path)
        return response

    async def _post(self, path: str, body: dict) -> httpx.Response:
        """Perform a POST request with standardised error handling."""
        client = self._get_client()
        try:
            response = await client.post(path, json=body)
        except httpx.ConnectError:
            raise LangflowConnectionError(self._base_url) from None
        except httpx.TimeoutException:
            raise LangflowTimeoutError(self._timeout) from None
        except httpx.RequestError as exc:
            raise LangflowConnectionError(self._base_url) from exc
        self._raise_for_status(response, path)
        return response

    def _raise_for_status(self, response: httpx.Response, path: str) -> None:
        if response.status_code == 404:
            raise LangflowFlowNotFoundError(path)
        if response.status_code >= 400:
            # Log status code for debugging but do NOT log full response body
            # to avoid leaking sensitive retrieved content or system prompts.
            logger.warning("Langflow HTTP error on %s: status=%d", path, response.status_code)
            raise LangflowResponseError(response.status_code, detail=response.text)

    # ── Public API ────────────────────────────────────────────────────────────

    async def health_check(self) -> LangflowHealthResponse:
        """
        Check if Langflow is reachable and healthy.

        Uses GET /health_check (Langflow ≥ 1.x).
        Raises LangflowConnectionError / LangflowTimeoutError on failure.
        """
        if not self._base_url:
            raise LangflowConnectionError(None)
        response = await self._get("/health_check")
        try:
            data = response.json()
            return LangflowHealthResponse(**data)
        except Exception:
            # If the response doesn't match the schema, treat as healthy
            # as long as the status code was 2xx.
            return LangflowHealthResponse(status="ok")

    async def get_version(self) -> LangflowVersionResponse:
        """
        Get the Langflow version.

        Uses GET /api/v1/version.
        """
        response = await self._get("/api/v1/version")
        try:
            return LangflowVersionResponse(**response.json())
        except Exception:
            return LangflowVersionResponse()

    async def list_flows(self) -> list[dict]:
        """
        List all flows available in the Langflow instance.

        Uses GET /api/v1/flows.
        Returns a list of flow metadata dicts.
        """
        response = await self._get("/api/v1/flows")
        data = response.json()
        if isinstance(data, list):
            return data
        # Langflow may wrap in a "flows" key
        return data.get("flows", [])

    async def upload_file(
        self,
        flow_id: str,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to Langflow using its official files upload API.

        Uses POST /api/v1/files/upload/{flow_id}.
        Returns the file_path inside Langflow container.
        """
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        files = {"file": (filename, file_content, content_type)}
        path = f"/api/v1/files/upload/{flow_id}"

        async with httpx.AsyncClient(
            base_url=self._base_url, headers=headers, timeout=self._timeout
        ) as upload_client:
            try:
                response = await upload_client.post(path, files=files)
            except httpx.ConnectError:
                raise LangflowConnectionError(self._base_url) from None
            except httpx.TimeoutException:
                raise LangflowTimeoutError(self._timeout) from None
            except httpx.RequestError as exc:
                raise LangflowConnectionError(self._base_url) from exc
            self._raise_for_status(response, path)
            data = response.json()
            return data.get("file_path", "")

    async def run_flow(
        self,
        flow_id: str,
        request: LangflowRunRequest,
    ) -> LangflowRunResponse:
        """
        Execute a Langflow flow.

        Uses POST /api/v1/run/{flow_id}.

        The `request.tweaks` field MUST contain server-side injected values
        such as course_id — never values sourced directly from user input
        (PRD RAG-03, docs/ai.md section 7).

        Args:
            flow_id:  UUID of the Langflow flow to execute.
            request:  Run parameters including input_value and tweaks.

        Returns:
            LangflowRunResponse with the flow output.

        Raises:
            LangflowFlowNotFoundError: if the flow_id does not exist.
            LangflowConnectionError:   if Langflow is unreachable.
            LangflowTimeoutError:      if the request times out.
            LangflowResponseError:     if Langflow returns an HTTP error.
        """
        path = f"/api/v1/run/{flow_id}"
        # Log the path and flow_id (safe) but NOT the full request body,
        # which may contain retrieved document content.
        logger.info("LangflowClient: running flow %s", flow_id)

        body = request.model_dump(exclude_none=True)
        response = await self._post(path, body)

        try:
            data = response.json()
            return LangflowRunResponse(**data)
        except Exception as exc:
            logger.warning("LangflowClient: failed to parse flow response: %s", exc)
            raise LangflowResponseError(response.status_code, "Invalid response format") from exc


# ── FastAPI dependency ────────────────────────────────────────────────────────


async def get_langflow_client() -> LangflowClient:
    """
    FastAPI dependency that yields a configured LangflowClient.

    Usage in endpoints:
        async def my_endpoint(
            lf: LangflowClient = Depends(get_langflow_client)
        ): ...
    """
    async with LangflowClient() as client:
        yield client
