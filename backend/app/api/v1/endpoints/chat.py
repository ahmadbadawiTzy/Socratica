"""
Chat endpoints — conversations, messages, RAG via Langflow.

Flow:
  POST /conversations          → create conversation
  GET  /conversations          → list user's conversations
  GET  /conversations/{id}     → get conversation with messages
  POST /conversations/{id}/messages → send message → Langflow RAG → response
  DELETE /conversations/{id}   → soft-delete conversation
"""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.models import (
    Conversation,
    ConversationMode,
    Enrollment,
    Escalation,
    EscalationStatus,
    Message,
    MessageRole,
    User,
)
from app.services.health_monitor import health_monitor
from app.services.langflow.client import LangflowClient
from app.services.langflow.exceptions import LangflowError
from app.services.langflow.schemas import LangflowRunRequest

logger = get_logger(__name__)
router = APIRouter(prefix="/conversations")


# ── Schemas ───────────────────────────────────────────────────────────────────


class CitationItem(BaseModel):
    document_name: str
    page: str | None = None
    section: str | None = None
    chunk_id: str | None = None
    document_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationItem] | None = None
    meta: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    course_id: str
    title: str | None
    mode: str
    is_active: bool
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: str
    course_id: str
    title: str | None
    mode: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateConversationRequest(BaseModel):
    course_id: str
    mode: str = "qa"
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str
    mode: str | None = None  # override conversation mode for this message


class SendMessageResponse(BaseModel):
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    content: str
    citations: list[CitationItem] = []
    mode: str
    status: str  # answered | insufficient_context | out_of_scope | escalated | error | quota_exceeded | authentication_error | rate_limited | not_connected | connection_timeout | service_error
    error_code: str | None = None
    error_message: str | None = None
    escalation_id: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _assert_enrolled(user_id: str, course_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enrolled in this course.")


def _pick_flow_id(mode: str) -> str | None:
    """Return the configured flow ID for the given mode."""
    if settings.langflow_unified_flow_id:
        return settings.langflow_unified_flow_id
    mapping = {
        "qa": settings.langflow_retrieval_flow_id,
        "socratic": settings.langflow_socratic_flow_id,
        "evaluator": settings.langflow_evaluator_flow_id,
    }
    return mapping.get(mode)


def _parse_citations(langflow_response: dict) -> list[dict]:
    """
    Extract citation metadata from Langflow response.
    Citations must come from actual retrieved chunks; never fabricated.
    """
    citations = []
    try:
        for output in langflow_response.get("outputs", []):
            for item in output.get("outputs", []):
                artifacts = item.get("artifacts", {})
                raw_cits = artifacts.get("citations", [])
                if isinstance(raw_cits, list):
                    citations.extend(raw_cits)
                # Also check results.message.data.citations
                results = item.get("results", {})
                if isinstance(results, dict):
                    msg = results.get("message", {})
                    if isinstance(msg, dict):
                        data = msg.get("data", {})
                        if isinstance(data, dict):
                            more = data.get("citations", [])
                            if isinstance(more, list):
                                citations.extend(more)
                    # Check for retrieved chunks/records in results
                    records = results.get("data") or results.get("records") or artifacts.get("chunks")
                    if isinstance(records, list):
                        for rec in records:
                            meta = rec.get("data", {}) if isinstance(rec, dict) else {}
                            if meta and ("document_name" in meta or "document_id" in meta):
                                citations.append({
                                    "document_name": meta.get("document_name", "Course Material"),
                                    "page": str(meta.get("page", "")) if meta.get("page") else None,
                                    "section": str(meta.get("section", "")) if meta.get("section") else None,
                                    "chunk_id": str(meta.get("chunk_id", "")) if meta.get("chunk_id") else None,
                                    "document_id": str(meta.get("document_id", "")) if meta.get("document_id") else None,
                                })
    except (KeyError, TypeError):
        pass
    return citations


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", response_model=ConversationListItem, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Conversation:
    await _assert_enrolled(user.id, body.course_id, db)
    mode = (
        ConversationMode(body.mode)
        if body.mode in ConversationMode.__members__.values()
        else ConversationMode.QA
    )
    conv = Conversation(
        user_id=user.id,
        course_id=body.course_id,
        mode=mode,
        title=body.title,
    )
    db.add(conv)
    await db.flush()
    return conv


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id, Conversation.is_active.is_(True))
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    conv.is_active = False


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SendMessageResponse:
    """
    Send a message in a conversation.

    Flow:
      1. Validate user owns conversation and is enrolled in the course.
      2. Save user message.
      3. Call Langflow RAG flow with course_id from authorization (never from user input).
      4. Parse response: answer, citations, status.
      5. Save assistant message.
      6. Create escalation record if needed.
      7. Return response.
    """
    # Load conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.is_active.is_(True),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Verify enrollment (course_id from DB, not user input)
    await _assert_enrolled(user.id, conv.course_id, db)

    effective_mode = body.mode or conv.mode.value
    flow_id = _pick_flow_id(effective_mode)

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # Call Langflow
    answer_text = ""
    citations: list[dict] = []
    response_status = "error"
    escalation_id: str | None = None
    meta: dict = {"mode": effective_mode, "flow_id": flow_id}

    if not flow_id or not settings.langflow_base_url:
        answer_text = (
            "Sistem sedang dalam konfigurasi. Langflow flow belum dikonfigurasi. "
            "Silakan hubungi administrator."
        )
        response_status = "error"
        meta["error"] = "Langflow flow not configured"
        logger.warning("No flow_id configured for mode=%s", effective_mode)
    else:
        start = time.monotonic()
        try:
            input_content = body.content
            if settings.langflow_unified_flow_id and not input_content.startswith(f"[MODE: {effective_mode}]"):
                input_content = f"[MODE: {effective_mode}] {input_content}"

            async with LangflowClient() as lf:
                lf_response = await lf.run_flow(
                    flow_id,
                    LangflowRunRequest(
                        input_value=input_content,
                        session_id=conversation_id,
                        tweaks={
                            # course_id injected server-side from authorization (PRD RAG-03)
                            "qdrant-retriever": {"course_id": str(conv.course_id)},
                        },
                    ),
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            meta["latency_ms"] = latency_ms

            # Extract text output
            answer_text = lf_response.extract_text_output() or ""

            # Extract status from response metadata if available
            raw = lf_response.model_dump()
            citations = _parse_citations(raw)

            error_code: str | None = None
            error_message: str | None = None

            # Determine response status
            if not answer_text or answer_text.strip() == "":
                response_status = "insufficient_context"
                answer_text = (
                    "Maaf, saya tidak menemukan informasi yang cukup untuk menjawab "
                    "pertanyaan ini berdasarkan materi mata kuliah. Pertanyaan Anda "
                    "akan diteruskan ke dosen/asisten dosen."
                )
            else:
                response_status = "answered"
                health_monitor.record_chat_success()

        except Exception as exc:
            classification = health_monitor.record_failure(exc)
            logger.warning(
                "Langflow/Gemini error for conversation %s: [%s] %s",
                conversation_id,
                classification.code,
                classification.user_message,
            )
            answer_text = classification.user_message
            response_status = classification.status.value
            error_code = classification.code
            error_message = classification.user_message
            meta["error"] = classification.code
            meta["error_message"] = classification.user_message

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=answer_text,
        citations=citations or None,
        meta=meta,
    )
    db.add(assistant_msg)
    await db.flush()

    # Create escalation if needed
    if response_status in (
        "insufficient_context",
        "error",
        "quota_exceeded",
        "authentication_error",
        "rate_limited",
        "not_connected",
        "connection_timeout",
        "service_error",
    ):
        escalation = Escalation(
            conversation_id=conversation_id,
            user_id=user.id,
            course_id=conv.course_id,
            question=body.content,
            reason=response_status,
            context_summary=f"Mode: {effective_mode}. Answer status: {response_status}.",
            status=EscalationStatus.PENDING,
        )
        db.add(escalation)
        await db.flush()
        escalation_id = escalation.id

    return SendMessageResponse(
        conversation_id=conversation_id,
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        content=answer_text,
        citations=[CitationItem(**c) for c in citations if isinstance(c, dict)],
        mode=effective_mode,
        status=response_status,
        error_code=error_code,
        error_message=error_message,
        escalation_id=escalation_id,
    )
