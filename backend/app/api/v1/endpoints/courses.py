"""Course endpoints — list, create, detail, enrollment."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.rbac import UserRole
from app.db.session import get_db_session
from app.models.models import Course, CourseRole, Enrollment, User

router = APIRouter(prefix="/courses")


class CourseResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    is_active: bool
    model_config = {"from_attributes": True}


class CourseCreateRequest(BaseModel):
    code: str
    name: str
    description: str | None = None


class EnrollRequest(BaseModel):
    user_id: str
    course_role: str = "student"


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[Course]:
    """List courses the current user is enrolled in."""
    result = await db.execute(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user.id, Course.is_active.is_(True))
    )
    return list(result.scalars().all())


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Course:
    """Create a new course. Only lecturers/admin can create."""
    if user.system_role not in (UserRole.LECTURER, "admin"):
        raise HTTPException(status_code=403, detail="Only lecturers can create courses.")
    existing = await db.execute(select(Course).where(Course.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Course code already exists.")
    course = Course(code=body.code, name=body.name, description=body.description)
    db.add(course)
    await db.flush()
    # Auto-enroll creator as lecturer
    enrollment = Enrollment(user_id=user.id, course_id=course.id, course_role=CourseRole.LECTURER)
    db.add(enrollment)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Course:
    enr = await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id)
    )
    if not enr.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enrolled in this course.")
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_user(
    course_id: str,
    body: EnrollRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Enroll a user in a course. Only lecturer/TA of the course can do this."""
    enr = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
            Enrollment.course_role.in_([CourseRole.LECTURER, CourseRole.TA]),
        )
    )
    if not enr.scalar_one_or_none() and user.system_role not in (UserRole.LECTURER, "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permission.")
    role = (
        CourseRole(body.course_role)
        if body.course_role in CourseRole.__members__.values()
        else CourseRole.STUDENT
    )
    new_enr = Enrollment(user_id=body.user_id, course_id=course_id, course_role=role)
    db.add(new_enr)
    return {"message": "Enrolled successfully."}
