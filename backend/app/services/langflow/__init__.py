"""
Langflow service package.

Provides LangflowClient for communicating with the Langflow instance
running in Docker. FastAPI uses this client to call RAG flows.

Architecture (docs/prd.md section 10.2):
  FastAPI Backend → Langflow → Retriever → Vector DB → LLM → Response
"""

from app.services.langflow.client import LangflowClient
from app.services.langflow.exceptions import (
    LangflowConnectionError,
    LangflowError,
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

__all__ = [
    "LangflowClient",
    "LangflowConnectionError",
    "LangflowError",
    "LangflowFlowNotFoundError",
    "LangflowResponseError",
    "LangflowTimeoutError",
    "LangflowHealthResponse",
    "LangflowRunRequest",
    "LangflowRunResponse",
    "LangflowVersionResponse",
]
