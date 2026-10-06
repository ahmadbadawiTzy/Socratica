"""
RBAC — Role and permission definitions for Socratica.

Roles (PRD section 6):
  student   — enrolled student; accesses own courses, asks questions.
  ta        — Teaching Assistant; manages assigned course, handles escalations.
  lecturer  — Course owner; manages course KB, handles escalations.
  admin     — [DECISION REQUIRED] OD-12: whether admin role is needed in V1.

Permission model:
  Permissions are evaluated SERVER-SIDE on every request (docs/ai.md section 7,
  PRD SEC-05). Client claims are NEVER trusted without server-side verification.

  course_id for retrieval is ALWAYS derived from the authorization context, not
  from user input or LLM output (PRD RAG-03, docs/ai.md section 7).

Note: Full permission enforcement (JWT validation, enrollment lookup) is
implemented in Phase 2 after OD-02 (auth method) is decided.
This module defines the shared enums and capability constants used across the app.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """User roles in the Socratica system."""

    STUDENT = "student"
    TA = "ta"
    LECTURER = "lecturer"
    # [DECISION REQUIRED] OD-12 — admin role existence in V1.
    # ADMIN = "admin"


class CoursePermission(StrEnum):
    """
    Granular permissions evaluated per (user, course) pair.

    Each API endpoint declares which permission(s) it requires.
    The permission check MUST be performed server-side; client-supplied
    role claims must be re-verified against the database.
    """

    # Student capabilities
    ASK_QUESTION = "ask_question"
    VIEW_OWN_CHAT_HISTORY = "view_own_chat_history"
    UPLOAD_DRAFT = "upload_draft"

    # Lecturer / TA capabilities
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"
    MANAGE_KNOWLEDGE_BASE = "manage_knowledge_base"
    VIEW_STUDENT_QUESTIONS = "view_student_questions"
    HANDLE_ESCALATION = "handle_escalation"
    VIEW_DASHBOARD = "view_dashboard"


# ── Baseline permission map ───────────────────────────────────────────────────
# Maps each role to the set of permissions it holds.
# Differences between lecturer and ta are [DECISION REQUIRED] (OD-12).
# Until decided, both hold the same set of permissions.

ROLE_PERMISSIONS: dict[UserRole, frozenset[CoursePermission]] = {
    UserRole.STUDENT: frozenset(
        {
            CoursePermission.ASK_QUESTION,
            CoursePermission.VIEW_OWN_CHAT_HISTORY,
            CoursePermission.UPLOAD_DRAFT,
        }
    ),
    UserRole.TA: frozenset(
        {
            # TAs can also ask questions for testing purposes (PRD table section 6)
            CoursePermission.ASK_QUESTION,
            CoursePermission.UPLOAD_DOCUMENT,
            CoursePermission.DELETE_DOCUMENT,
            CoursePermission.MANAGE_KNOWLEDGE_BASE,
            CoursePermission.VIEW_STUDENT_QUESTIONS,
            CoursePermission.HANDLE_ESCALATION,
            CoursePermission.VIEW_DASHBOARD,
        }
    ),
    UserRole.LECTURER: frozenset(
        {
            CoursePermission.ASK_QUESTION,
            CoursePermission.UPLOAD_DOCUMENT,
            CoursePermission.DELETE_DOCUMENT,
            CoursePermission.MANAGE_KNOWLEDGE_BASE,
            CoursePermission.VIEW_STUDENT_QUESTIONS,
            CoursePermission.HANDLE_ESCALATION,
            CoursePermission.VIEW_DASHBOARD,
        }
    ),
}


def has_permission(role: UserRole, permission: CoursePermission) -> bool:
    """
    Return True if *role* holds *permission*.

    This is a pure capability check. It does NOT verify whether the user is
    enrolled in / assigned to a specific course. That check must be performed
    separately against the database (PRD SEC-05).
    """
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
