"""
Document endpoints — upload, list, status, delete.

Supports PDF, DOCX, PPTX. After upload, triggers ingestion via Langflow.
Course isolation enforced: only course members can upload/view documents.
Only lecturer/TA can upload or delete.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.models import (
    CourseRole,
    Document,
    DocumentType,
    Enrollment,
    IngestionStatus,
    User,
)
from app.services.langflow.client import LangflowClient
from app.services.langflow.exceptions import LangflowError

logger = get_logger(__name__)
router = APIRouter(prefix="/courses/{course_id}/documents")

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "md"}


class DocumentResponse(BaseModel):
    id: str
    course_id: str
    document_name: str
    original_filename: str
    document_type: str | None
    ingestion_status: str
    ingestion_error: str | None
    meeting: str | None
    chapter: str | None
    file_size_bytes: int | None
    model_config = {"from_attributes": True}


async def _assert_lecturer_or_ta(user_id: str, course_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
            Enrollment.course_role.in_([CourseRole.LECTURER, CourseRole.TA]),
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Only lecturers/TAs can manage documents.")


async def _assert_enrolled(user_id: str, course_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enrolled in this course.")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    course_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Document]:
    await _assert_enrolled(user.id, course_id, db)
    result = await db.execute(select(Document).where(Document.course_id == course_id))
    return list(result.scalars().all())


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    course_id: str,
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(default="other"),
    meeting: str = Form(default=None),
    chapter: str = Form(default=None),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Document:
    await _assert_lecturer_or_ta(user.id, course_id, db)

    # Validate file extension
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail=f"File type .{ext} not supported.")

    # Validate file size
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.upload_max_size_mb}MB.",
        )

    # Store file safely (never use user-supplied filename as path)
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.{ext}"
    storage_path = str(upload_dir / safe_name)
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    doc_type_val = (
        document_type if document_type in DocumentType.__members__.values() else DocumentType.OTHER
    )

    doc = Document(
        course_id=course_id,
        uploaded_by=user.id,
        original_filename=file.filename or safe_name,
        storage_path=storage_path,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        document_name=document_name,
        document_type=doc_type_val,
        meeting=meeting,
        chapter=chapter,
        ingestion_status=IngestionStatus.UPLOADED,
    )
    db.add(doc)
    await db.flush()

    # Trigger ingestion in Langflow (async, best-effort)
    ingestion_flow_id = settings.langflow_ingestion_flow_id or settings.langflow_unified_flow_id
    if ingestion_flow_id and settings.langflow_base_url:
        try:
            doc.ingestion_status = IngestionStatus.PROCESSING
            from app.services.langflow.schemas import LangflowRunRequest

            async with LangflowClient() as lf:
                lf_path = await lf.upload_file(
                    ingestion_flow_id,
                    file_content=content,
                    filename=file.filename or safe_name,
                    content_type=file.content_type or "application/octet-stream",
                )
                await lf.run_flow(
                    ingestion_flow_id,
                    LangflowRunRequest(
                        input_value=lf_path,
                        tweaks={
                            "file-input-1": {"path": lf_path},
                            "qdrant-1": {
                                "course_id": str(course_id),
                                "document_id": str(doc.id),
                                "document_name": document_name,
                            },
                            "qdrant-retriever": {
                                "course_id": str(course_id),
                                "document_id": str(doc.id),
                                "document_name": document_name,
                            },
                            "recursive-splitter-1": {
                                "course_id": str(course_id),
                                "document_id": str(doc.id),
                                "document_name": document_name,
                            },
                        },
                    ),
                )
            doc.ingestion_status = IngestionStatus.READY
            logger.info("Ingestion triggered for document %s", doc.id)
        except LangflowError as exc:
            logger.warning("Ingestion trigger failed for doc %s: %s", doc.id, exc.message)
            doc.ingestion_status = IngestionStatus.FAILED
            doc.ingestion_error = f"Langflow ingestion failed: {exc.message}"
        except Exception:
            logger.exception("Unexpected error triggering ingestion for doc %s", doc.id)
            doc.ingestion_status = IngestionStatus.FAILED
            doc.ingestion_error = "Unexpected ingestion error."
    else:
        logger.warning(
            "Ingestion flow not configured. Document %s saved but not indexed. "
            "Set LANGFLOW_UNIFIED_FLOW_ID in .env.",
            doc.id,
        )

    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    course_id: str,
    document_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Document:
    await _assert_enrolled(user.id, course_id, db)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.course_id == course_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    course_id: str,
    document_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await _assert_lecturer_or_ta(user.id, course_id, db)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.course_id == course_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from filesystem
    if doc.storage_path and os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except OSError:
            logger.warning("Could not remove file %s", doc.storage_path)

    await db.delete(doc)
    logger.info("Document %s deleted from course %s by user %s", document_id, course_id, user.id)
