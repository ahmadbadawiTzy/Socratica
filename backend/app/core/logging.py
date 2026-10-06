"""
Structured logging setup for Socratica.

Rules (from docs/ai.md section 11):
- Do NOT log passwords, API keys, access tokens, or sensitive personal data.
- Log IDs (request_id, chunk_id, document_id) and metrics, not full content.
- Use correlation IDs across FastAPI ↔ Langflow.
"""

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Configure root logger. Call once at application startup."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )
    # Suppress noisy third-party loggers in non-debug mode.
    if not settings.app_debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use __name__ as the name in each module."""
    return logging.getLogger(name)
