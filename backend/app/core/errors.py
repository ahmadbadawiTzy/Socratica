"""
Centralised exception handlers and custom error types for Socratica.

Security note (docs/ai.md SEC-08/SEC-09):
- Error responses MUST NOT expose internal stack traces, system prompt,
  secret values, or data from other users/courses.
- In production (app_debug=False) only a safe, human-readable message is
  returned. The full detail is logged server-side with a correlation ID.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────


class SocraticaError(Exception):
    """Base exception for all Socratica application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(SocraticaError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found."


class ForbiddenError(SocraticaError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access denied."


class UnauthorizedError(SocraticaError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required."


class ValidationError(SocraticaError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Validation error."


class ServiceUnavailableError(SocraticaError):
    """Raised when a downstream service (Langflow, Vector DB, LLM) is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "A required service is currently unavailable. Please try again later."


# ── Handler registration ──────────────────────────────────────────────────────


def _safe_error_response(
    request: Request,
    error_id: str,
    status_code: int,
    message: str,
) -> JSONResponse:
    """Build a JSON error response that is safe to send to the client."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "id": error_id,
                "message": message,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""

    @app.exception_handler(SocraticaError)
    async def socratica_error_handler(request: Request, exc: SocraticaError) -> JSONResponse:
        error_id = str(uuid.uuid4())
        logger.warning(
            "Application error [%s] on %s %s: %s",
            error_id,
            request.method,
            request.url.path,
            exc.detail,
        )
        return _safe_error_response(request, error_id, exc.status_code, exc.detail)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        error_id = str(uuid.uuid4())
        logger.exception(
            "Unhandled error [%s] on %s %s",
            error_id,
            request.method,
            request.url.path,
        )
        # Do not expose exc details to the client in any environment.
        return _safe_error_response(
            request,
            error_id,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred. Please try again later.",
        )
