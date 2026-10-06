"""
Custom exceptions for the Langflow service layer.

These wrap httpx/network exceptions into domain-level errors so that
upstream FastAPI handlers can produce safe, client-friendly responses
without leaking internal implementation details (docs/ai.md SEC-08).
"""


class LangflowError(Exception):
    """Base exception for all Langflow communication errors."""

    def __init__(self, message: str = "Langflow error") -> None:
        self.message = message
        super().__init__(message)


class LangflowConnectionError(LangflowError):
    """
    Raised when the Langflow service cannot be reached.

    Common causes: Docker container not running, wrong hostname/port,
    network misconfiguration.
    """

    def __init__(self, url: str | None = None) -> None:
        detail = f"Cannot connect to Langflow at {url}" if url else "Cannot connect to Langflow"
        super().__init__(detail)


class LangflowTimeoutError(LangflowError):
    """Raised when a Langflow request exceeds the configured timeout."""

    def __init__(self, timeout: float | None = None) -> None:
        detail = (
            f"Langflow request timed out after {timeout}s"
            if timeout
            else "Langflow request timed out"
        )
        super().__init__(detail)


class LangflowResponseError(LangflowError):
    """
    Raised when Langflow returns an HTTP error status or an unexpected response.

    The raw status code is stored for logging purposes but MUST NOT be
    forwarded to the client as-is (to avoid leaking internal details).
    """

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Langflow returned HTTP {status_code}")


class LangflowFlowNotFoundError(LangflowError):
    """Raised when the requested flow ID does not exist in Langflow."""

    def __init__(self, flow_id: str) -> None:
        self.flow_id = flow_id
        super().__init__(f"Langflow flow not found: {flow_id}")
