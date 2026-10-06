"""
Service status and error classification for Langflow and Gemini communication.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import NamedTuple


class ServiceStatus(str, Enum):
    CONNECTED = "connected"
    NOT_CONNECTED = "not_connected"
    CONNECTION_TIMEOUT = "connection_timeout"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    SERVICE_ERROR = "service_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorClassification(NamedTuple):
    status: ServiceStatus
    code: str
    ui_title: str
    user_message: str


# Regexp patterns to sanitize sensitive credentials from any messages/logs
_SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"AQ\.[0-9A-Za-z-_]{30,}"),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
]


def sanitize_text(text: str | None) -> str:
    """Strip any accidental credential strings from text."""
    if not text:
        return ""
    sanitized = text
    for p in _SECRET_PATTERNS:
        sanitized = p.sub("[REDACTED]", sanitized)
    return sanitized


def classify_error(
    status_code: int | None = None,
    error_text: str | None = None,
    exc: Exception | None = None,
) -> ErrorClassification:
    """
    Classify an error into a standardized ServiceStatus according to actual service conditions.

    Rules:
    - 401, 403 or invalid API key -> AUTHENTICATION_ERROR
    - 429 or quota exceeded / resource exhausted -> QUOTA_EXCEEDED (or RATE_LIMITED if transient RPM)
    - ConnectError / connection refused / 502 / 503 / 504 -> NOT_CONNECTED
    - TimeoutException / timeout -> CONNECTION_TIMEOUT
    - 500 / flow handle / graph error -> SERVICE_ERROR
    - Others -> UNKNOWN_ERROR
    """
    combined_text = sanitize_text(f"{error_text or ''} {str(exc) if exc else ''}").lower()

    # 1. Connection timeouts
    if "timeout" in combined_text or "timed out" in combined_text:
        return ErrorClassification(
            status=ServiceStatus.CONNECTION_TIMEOUT,
            code="CONNECTION_TIMEOUT",
            ui_title="Connection Timeout",
            user_message=(
                "Service membutuhkan waktu terlalu lama untuk merespons. "
                "Silakan coba beberapa saat lagi."
            ),
        )

    # 2. Connection refused / Langflow unavailable
    if (
        "connecterror" in combined_text
        or "connection refused" in combined_text
        or "cannot connect" in combined_text
        or "failed to connect" in combined_text
        or "connection error" in combined_text
        or status_code in (502, 503, 504)
    ):
        return ErrorClassification(
            status=ServiceStatus.NOT_CONNECTED,
            code="NOT_CONNECTED",
            ui_title="Not Connected",
            user_message="Langflow tidak dapat diakses. Pastikan service Langflow aktif.",
        )

    # 3. Authentication / API Key rejected
    if (
        status_code in (401, 403)
        or "api_key_invalid" in combined_text
        or "api key not valid" in combined_text
        or "invalid api key" in combined_text
        or "unauthenticated" in combined_text
        or "permission_denied" in combined_text
        or "api key is required" in combined_text
        or "google api key is required" in combined_text
    ):
        return ErrorClassification(
            status=ServiceStatus.AUTHENTICATION_ERROR,
            code="AUTHENTICATION_ERROR",
            ui_title="Authentication Error",
            user_message=(
                "Credential Gemini tidak valid atau ditolak. "
                "Pastikan API key telah dikonfigurasi dengan benar di Langflow."
            ),
        )

    # 4. Quota Exceeded vs Rate Limited
    is_429 = status_code == 429 or "429" in combined_text
    is_resource_exhausted = "resource_exhausted" in combined_text

    if is_429 or is_resource_exhausted or "quota" in combined_text:
        # Check if it is a transient rate limit (per minute / RPM / TPM) without quota exhaustion
        is_transient_rate_limit = (
            ("rate limit" in combined_text or "rate_limit" in combined_text or "too many requests" in combined_text)
            and "quota" not in combined_text
            and "exceeded your current quota" not in combined_text
            and "plan and billing" not in combined_text
        )

        if is_transient_rate_limit:
            return ErrorClassification(
                status=ServiceStatus.RATE_LIMITED,
                code="RATE_LIMITED",
                ui_title="Rate Limited",
                user_message=(
                    "Batas laju permintaan Gemini telah tercapai (Rate Limit). "
                    "Silakan tunggu sejenak sebelum mencoba kembali."
                ),
            )

        # Default to quota exceeded for resource exhausted / quota messages
        return ErrorClassification(
            status=ServiceStatus.QUOTA_EXCEEDED,
            code="QUOTA_EXCEEDED",
            ui_title="Quota Exceeded",
            user_message=(
                "Gemini API quota telah habis. Silakan gunakan kembali setelah "
                "quota tersedia atau konfigurasi credential Gemini yang valid di Langflow."
            ),
        )

    # 5. Service / Flow execution error
    if (
        status_code == 500
        or "invalid handles" in combined_text
        or "flow error" in combined_text
        or "langflow error" in combined_text
    ):
        return ErrorClassification(
            status=ServiceStatus.SERVICE_ERROR,
            code="SERVICE_ERROR",
            ui_title="Service Error",
            user_message=(
                "Terjadi kesalahan pada alur pemrosesan Langflow (Service Error). "
                "Silakan coba lagi atau hubungi administrator sistem."
            ),
        )

    # 6. Fallback Unknown error
    return ErrorClassification(
        status=ServiceStatus.UNKNOWN_ERROR,
        code="UNKNOWN_ERROR",
        ui_title="Unknown Error",
        user_message="Terjadi kesalahan tidak terduga saat memproses pertanyaan Anda.",
    )
