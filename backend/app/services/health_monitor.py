"""
Service health monitor for Langflow and Gemini communication.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.services.langflow.classifier import (
    ErrorClassification,
    ServiceStatus,
    classify_error,
)
from app.services.langflow.client import LangflowClient
from app.services.langflow.schemas import LangflowRunRequest

logger = get_logger(__name__)


class ServiceHealthMonitor:
    """
    Central monitor for actual Langflow and Gemini operational status.
    Ensures that status is ALWAYS derived from real communication,
    with no fake recovery (a failed Gemini status will not revert to connected
    without a successful actual probe/request).
    """

    def __init__(self) -> None:
        self.langflow_status: ServiceStatus = ServiceStatus.UNKNOWN_ERROR
        self.gemini_status: ServiceStatus = ServiceStatus.UNKNOWN_ERROR
        self.last_checked: datetime | None = None
        self.last_error: ErrorClassification | None = None
        self._lock = asyncio.Lock()

    def record_chat_success(self) -> None:
        """Mark both Langflow and Gemini as Connected after a real chat execution."""
        self.langflow_status = ServiceStatus.CONNECTED
        self.gemini_status = ServiceStatus.CONNECTED
        self.last_error = None
        self.last_checked = datetime.now(timezone.utc)

    def record_failure(
        self,
        exc: Exception,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> ErrorClassification:
        """Record and classify an actual runtime failure from chat or ingestion."""
        code = status_code or getattr(exc, "status_code", None)
        text = detail or getattr(exc, "detail", getattr(exc, "message", str(exc)))
        classification = classify_error(code, text, exc)

        self.last_error = classification
        self.last_checked = datetime.now(timezone.utc)

        if classification.status in (ServiceStatus.NOT_CONNECTED, ServiceStatus.CONNECTION_TIMEOUT):
            self.langflow_status = classification.status
            # When Langflow is down/timing out, Gemini reachability via Langflow is unknown
            self.gemini_status = ServiceStatus.UNKNOWN_ERROR
        else:
            # Langflow answered but Gemini or flow failed
            self.langflow_status = ServiceStatus.CONNECTED
            self.gemini_status = classification.status

        return classification

    async def check_health(self, force_probe: bool = False) -> dict[str, Any]:
        """
        Probe real services and generate comprehensive health report.
        """
        async with self._lock:
            # 1. Probe Langflow directly
            if not settings.langflow_base_url:
                self.langflow_status = ServiceStatus.NOT_CONNECTED
                self.gemini_status = ServiceStatus.UNKNOWN_ERROR
                return self._build_report()

            langflow_up = False
            try:
                async with LangflowClient() as client:
                    await client.health_check()
                langflow_up = True
                self.langflow_status = ServiceStatus.CONNECTED
            except Exception as exc:
                self.record_failure(exc)
                return self._build_report()

            # 2. Determine Gemini state
            # Probe Gemini when explicitly requested (force_probe=True)
            # or when unknown and force_probe is enabled.
            # Real chat requests automatically update gemini_status with 0 extra overhead.
            should_probe_gemini = force_probe and langflow_up

            if should_probe_gemini and langflow_up:
                flow_id = settings.langflow_unified_flow_id
                if flow_id:
                    try:
                        async with LangflowClient() as client:
                            resp = await client.run_flow(
                                flow_id,
                                LangflowRunRequest(
                                    input_value="ping",
                                    session_id="health-probe",
                                ),
                            )
                            answer = resp.extract_text_output()
                            if answer:
                                self.gemini_status = ServiceStatus.CONNECTED
                                self.last_error = None
                            else:
                                self.gemini_status = ServiceStatus.SERVICE_ERROR
                    except Exception as exc:
                        self.record_failure(exc)

            self.last_checked = datetime.now(timezone.utc)
            return self._build_report()

    def _build_report(self) -> dict[str, Any]:
        # Overall status calculation
        if self.langflow_status != ServiceStatus.CONNECTED:
            overall = self.langflow_status.value
        elif self.gemini_status == ServiceStatus.CONNECTED:
            overall = "connected"
        elif self.gemini_status in (ServiceStatus.QUOTA_EXCEEDED, ServiceStatus.RATE_LIMITED):
            overall = "degraded"
        elif self.gemini_status == ServiceStatus.AUTHENTICATION_ERROR:
            overall = "authentication_error"
        elif self.gemini_status == ServiceStatus.SERVICE_ERROR:
            overall = "service_error"
        else:
            overall = "degraded" if self.gemini_status != ServiceStatus.UNKNOWN_ERROR else "connected"

        gemini_str = (
            "unknown"
            if self.gemini_status == ServiceStatus.UNKNOWN_ERROR
            else self.gemini_status.value
        )

        return {
            "status": overall,
            "service": settings.app_name,
            "langflow": {
                "status": self.langflow_status.value,
            },
            "gemini": {
                "status": gemini_str,
            },
            "error": {
                "code": self.last_error.code,
                "message": self.last_error.user_message,
            }
            if self.last_error
            else None,
        }


# Global singleton monitor
health_monitor = ServiceHealthMonitor()
