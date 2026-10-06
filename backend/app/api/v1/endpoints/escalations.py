"""Escalation endpoints — view and update escalations."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.session import get_db_session
from app.models.models import CourseRole, Enrollment, Escalation, EscalationStatus, User

router = APIRouter(prefix="/escalations")


class EscalationResponse(BaseModel):
    id: str
    conversation_id: str
    course_id: str
    question: str
    reason: str
    context_summary: str | None
    status: str
    resolution_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateEscalationRequest(BaseModel):
    status: str
    resolution_note: str | None = None


@router.get("", response_model=list[EscalationResponse])
async def list_my_escalations(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Escalation]:
    """Student: list own escalations."""
    result = await db.execute(
        select(Escalation)
        .where(Escalation.user_id == user.id)
        .order_by(Escalation.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/course/{course_id}", response_model=list[EscalationResponse])
async def list_course_escalations(
    course_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Escalation]:
    """Lecturer/TA: list all escalations for a course."""
    enr = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
            Enrollment.course_role.in_([CourseRole.LECTURER, CourseRole.TA]),
        )
    )
    if not enr.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied.")
    result = await db.execute(
        select(Escalation)
        .where(Escalation.course_id == course_id)
        .order_by(Escalation.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/{escalation_id}", response_model=EscalationResponse)
async def update_escalation(
    escalation_id: str,
    body: UpdateEscalationRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Escalation:
    """Lecturer/TA: update escalation status."""
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    esc = result.scalar_one_or_none()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found.")
    # Verify lecturer/TA access
    enr = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == esc.course_id,
            Enrollment.course_role.in_([CourseRole.LECTURER, CourseRole.TA]),
        )
    )
    if not enr.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied.")
    new_status = (
        EscalationStatus(body.status)
        if body.status in EscalationStatus.__members__.values()
        else None
    )
    if not new_status:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}")
    esc.status = new_status
    esc.resolved_by = user.id
    if body.resolution_note:
        esc.resolution_note = body.resolution_note
    return esc
