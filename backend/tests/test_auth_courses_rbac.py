"""
Integration tests for Authentication, Authorization, RBAC, and Course Isolation.
Tests run against the live PostgreSQL database.
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_auth_and_course_lifecycle_and_rbac(client: AsyncClient):
    import uuid
    suffix = uuid.uuid4().hex[:6]
    
    # 1. Register student
    student_email = f"student_{suffix}@univ.ac.id"
    res = await client.post("/api/v1/auth/register", json={
        "email": student_email,
        "password": "Password123!",
        "display_name": "Budi Student",
        "role": "student"
    })
    assert res.status_code == 201
    student_data = res.json()
    assert student_data["email"] == student_email
    assert student_data["system_role"] == "student"
    student_id = student_data["id"]

    # 2. Register lecturer
    lecturer_email = f"lecturer_{suffix}@univ.ac.id"
    res = await client.post("/api/v1/auth/register", json={
        "email": lecturer_email,
        "password": "Password123!",
        "display_name": "Dr. Lecturer",
        "role": "lecturer"
    })
    assert res.status_code == 201
    lecturer_data = res.json()
    assert lecturer_data["system_role"] == "lecturer"

    # 3. Student cannot register with duplicate email
    res = await client.post("/api/v1/auth/register", json={
        "email": student_email,
        "password": "Password123!",
        "display_name": "Duplicate Student",
    })
    assert res.status_code == 400

    # 4. Login student
    res = await client.post("/api/v1/auth/login", json={
        "email": student_email,
        "password": "Password123!",
    })
    assert res.status_code == 200
    student_tokens = res.json()
    assert "access_token" in student_tokens
    assert "refresh_token" in student_tokens
    student_auth = {"Authorization": f"Bearer {student_tokens['access_token']}"}

    # 5. Login lecturer
    res = await client.post("/api/v1/auth/login", json={
        "email": lecturer_email,
        "password": "Password123!",
    })
    assert res.status_code == 200
    lecturer_tokens = res.json()
    lecturer_auth = {"Authorization": f"Bearer {lecturer_tokens['access_token']}"}

    # 6. Test profile endpoint /auth/me
    res = await client.get("/api/v1/auth/me", headers=student_auth)
    assert res.status_code == 200
    assert res.json()["id"] == student_id

    # 7. Test token refresh
    res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": student_tokens["refresh_token"]
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    # 8. Test invalid token rejection
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert res.status_code == 401

    # 9. Test expired token rejection
    expired_token = create_access_token(
        data={"sub": student_id, "email": student_email, "role": "student"},
        expires_delta=timedelta(seconds=-10)
    )
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401

    # 10. Student attempts to create course -> FORBIDDEN (403)
    course_code_1 = f"CS101_{suffix}"
    res = await client.post("/api/v1/courses", json={
        "code": course_code_1,
        "name": "Intro to Computer Science",
        "description": "Basics"
    }, headers=student_auth)
    assert res.status_code == 403

    # 11. Lecturer creates Course 1 -> SUCCESS (201)
    res = await client.post("/api/v1/courses", json={
        "code": course_code_1,
        "name": "Intro to Computer Science",
        "description": "Basics"
    }, headers=lecturer_auth)
    assert res.status_code == 201
    course_1 = res.json()
    course_1_id = course_1["id"]

    # 12. Lecturer creates Course 2 -> SUCCESS (201)
    course_code_2 = f"CS202_{suffix}"
    res = await client.post("/api/v1/courses", json={
        "code": course_code_2,
        "name": "Advanced Algorithms",
        "description": "Algorithms"
    }, headers=lecturer_auth)
    assert res.status_code == 201
    course_2 = res.json()
    course_2_id = course_2["id"]

    # 13. Student cannot access Course 1 before enrollment -> 403
    res = await client.get(f"/api/v1/courses/{course_1_id}", headers=student_auth)
    assert res.status_code == 403

    # 14. Lecturer enrolls student in Course 1
    res = await client.post(f"/api/v1/courses/{course_1_id}/enroll", json={
        "user_id": student_id,
        "course_role": "student"
    }, headers=lecturer_auth)
    assert res.status_code == 201

    # 15. Student can now access Course 1
    res = await client.get(f"/api/v1/courses/{course_1_id}", headers=student_auth)
    assert res.status_code == 200
    assert res.json()["code"] == course_code_1

    # 16. Cross-course isolation: Student CANNOT access Course 2 (not enrolled) -> 403
    res = await client.get(f"/api/v1/courses/{course_2_id}", headers=student_auth)
    assert res.status_code == 403

    # 17. Cross-course isolation: Student cannot list documents of Course 2 -> 403
    res = await client.get(f"/api/v1/courses/{course_2_id}/documents", headers=student_auth)
    assert res.status_code == 403

    # 18. Student cannot upload course documents (only lecturer/TA) -> 403
    res = await client.post(
        f"/api/v1/courses/{course_1_id}/documents",
        data={"document_name": "Lecture 1"},
        files={"file": ("lecture1.pdf", b"%PDF-1.4 dummy", "application/pdf")},
        headers=student_auth
    )
    assert res.status_code == 403
