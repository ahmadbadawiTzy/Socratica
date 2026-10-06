"""
Pydantic schemas for Langflow API request/response contracts.

These are based on the Langflow REST API (langflowai/langflow:latest).
Key API endpoints used:
  GET  /api/v1/version        → LangflowVersionResponse
  GET  /health_check          → LangflowHealthResponse (Langflow ≥ 1.x uses /health_check)
  POST /api/v1/run/{flow_id}  → LangflowRunResponse
  GET  /api/v1/flows          → list of flows

Reference: https://docs.langflow.org/api-reference-api-examples
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ── Version ───────────────────────────────────────────────────────────────────


class LangflowVersionResponse(BaseModel):
    """Response from GET /api/v1/version"""

    version: str = ""
    package: str = ""


# ── Health ────────────────────────────────────────────────────────────────────


class LangflowHealthResponse(BaseModel):
    """Response from GET /health_check"""

    status: str = "ok"


# ── Flow run ──────────────────────────────────────────────────────────────────


class LangflowInputValue(BaseModel):
    """
    A single input value sent to a Langflow flow component.

    Langflow /api/v1/run/{flow_id} accepts:
      { "input_value": "<question>", "input_type": "chat", "output_type": "chat" }
    """

    input_value: str
    input_type: str = "chat"
    output_type: str = "chat"
    # Optional: session_id for stateful conversations (Socratic Mode state)
    session_id: str | None = None
    # tweaks: per-component overrides (e.g. course_id filter on retriever)
    tweaks: dict[str, Any] = Field(default_factory=dict)


class LangflowRunRequest(BaseModel):
    """
    Request body for POST /api/v1/run/{flow_id}

    The `tweaks` field is used to inject server-side values like course_id
    into the retriever component — ensuring the filter CANNOT be bypassed
    via user input (PRD RAG-03, docs/ai.md section 7).
    """

    input_value: str
    input_type: str = "chat"
    output_type: str = "chat"
    session_id: str | None = None
    tweaks: dict[str, Any] = Field(default_factory=dict)


class LangflowOutputMessage(BaseModel):
    """A single message in a Langflow output."""

    message: str | dict[str, Any] | None = None
    type: str | None = None


class LangflowOutputData(BaseModel):
    """Data section of a flow output."""

    outputs: list[dict[str, Any]] = Field(default_factory=list)


class LangflowRunOutput(BaseModel):
    """A single output from a Langflow run result."""

    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: list[dict[str, Any]] = Field(default_factory=list)


class LangflowRunResponse(BaseModel):
    """
    Response from POST /api/v1/run/{flow_id}

    Langflow wraps the output in:
      { "outputs": [ { "inputs": {...}, "outputs": [...] } ], "session_id": "..." }
    """

    outputs: list[LangflowRunOutput] = Field(default_factory=list)
    session_id: str | None = None

    def extract_text_output(self) -> str | None:
        """
        Extract the primary text response from the Langflow output structure.

        Returns None if no text output can be found.
        This is a best-effort extraction; callers should handle None gracefully.
        """
        try:
            for run_output in self.outputs:
                for output_item in run_output.outputs:
                    # Langflow chat outputs are typically nested under
                    # outputs[0].outputs[0].results.message.text
                    results = output_item.get("results", {})
                    if isinstance(results, dict):
                        msg = results.get("message", {})
                        if isinstance(msg, dict):
                            text = msg.get("text") or msg.get("data", {}).get("text")
                            if text:
                                return str(text)
                        if isinstance(msg, str) and msg:
                            return msg
                    # Also try outputs[0].outputs[0].messages[0].message
                    messages = output_item.get("messages", [])
                    if messages and isinstance(messages, list):
                        first = messages[0]
                        if isinstance(first, dict):
                            return str(first.get("message", ""))
        except (KeyError, IndexError, TypeError):
            pass
        return None
