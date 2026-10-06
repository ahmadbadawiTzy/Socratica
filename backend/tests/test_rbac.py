"""
Tests for RBAC roles and permission model.

PRD section 6, docs/ai.md section 7.
"""

from __future__ import annotations

from app.core.rbac import CoursePermission, UserRole, has_permission


class TestUserRoles:
    def test_all_roles_defined(self) -> None:
        roles = {r.value for r in UserRole}
        assert "student" in roles
        assert "ta" in roles
        assert "lecturer" in roles

    def test_roles_are_strings(self) -> None:
        for role in UserRole:
            assert isinstance(role.value, str)


class TestStudentPermissions:
    def test_student_can_ask_question(self) -> None:
        assert has_permission(UserRole.STUDENT, CoursePermission.ASK_QUESTION)

    def test_student_can_view_own_chat(self) -> None:
        assert has_permission(UserRole.STUDENT, CoursePermission.VIEW_OWN_CHAT_HISTORY)

    def test_student_can_upload_draft(self) -> None:
        assert has_permission(UserRole.STUDENT, CoursePermission.UPLOAD_DRAFT)

    def test_student_cannot_upload_document(self) -> None:
        assert not has_permission(UserRole.STUDENT, CoursePermission.UPLOAD_DOCUMENT)

    def test_student_cannot_delete_document(self) -> None:
        assert not has_permission(UserRole.STUDENT, CoursePermission.DELETE_DOCUMENT)

    def test_student_cannot_manage_kb(self) -> None:
        assert not has_permission(UserRole.STUDENT, CoursePermission.MANAGE_KNOWLEDGE_BASE)

    def test_student_cannot_view_dashboard(self) -> None:
        assert not has_permission(UserRole.STUDENT, CoursePermission.VIEW_DASHBOARD)

    def test_student_cannot_handle_escalation(self) -> None:
        assert not has_permission(UserRole.STUDENT, CoursePermission.HANDLE_ESCALATION)


class TestLecturerPermissions:
    def test_lecturer_can_ask_question(self) -> None:
        """Lecturers can ask questions for testing purposes (PRD section 6)."""
        assert has_permission(UserRole.LECTURER, CoursePermission.ASK_QUESTION)

    def test_lecturer_can_upload_document(self) -> None:
        assert has_permission(UserRole.LECTURER, CoursePermission.UPLOAD_DOCUMENT)

    def test_lecturer_can_delete_document(self) -> None:
        assert has_permission(UserRole.LECTURER, CoursePermission.DELETE_DOCUMENT)

    def test_lecturer_can_manage_kb(self) -> None:
        assert has_permission(UserRole.LECTURER, CoursePermission.MANAGE_KNOWLEDGE_BASE)

    def test_lecturer_can_handle_escalation(self) -> None:
        assert has_permission(UserRole.LECTURER, CoursePermission.HANDLE_ESCALATION)

    def test_lecturer_can_view_dashboard(self) -> None:
        assert has_permission(UserRole.LECTURER, CoursePermission.VIEW_DASHBOARD)


class TestTAPermissions:
    """TA baseline is identical to Lecturer until OD-12 is resolved."""

    def test_ta_can_manage_kb(self) -> None:
        assert has_permission(UserRole.TA, CoursePermission.MANAGE_KNOWLEDGE_BASE)

    def test_ta_can_handle_escalation(self) -> None:
        assert has_permission(UserRole.TA, CoursePermission.HANDLE_ESCALATION)

    def test_ta_cannot_view_other_chat(self) -> None:
        """TA does NOT have VIEW_OWN_CHAT_HISTORY for other users (no such permission)."""
        # VIEW_OWN_CHAT_HISTORY is a student-only self-service permission.
        assert not has_permission(UserRole.TA, CoursePermission.VIEW_OWN_CHAT_HISTORY)


class TestPermissionIsolation:
    def test_unknown_role_returns_no_permissions(self) -> None:
        """has_permission must return False for unknown/unmapped roles gracefully."""
        # Pass a raw string that is not a UserRole — should return False, not raise.
        result = has_permission("unknown_role", CoursePermission.ASK_QUESTION)  # type: ignore[arg-type]
        assert result is False
