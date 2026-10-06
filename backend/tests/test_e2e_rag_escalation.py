"""
End-to-End Integration Test for Document Ingestion, Chat, and Human Escalation.
Runs against the live FastAPI app, PostgreSQL, and Langflow instance.
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_document_chat_escalation(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]

    # 1. Register and login lecturer
    lec_email = f"prof_{suffix}@socratica.edu"
    res = await client.post("/api/v1/auth/register", json={
        "email": lec_email,
        "password": "Password123!",
        "display_name": "Prof. Alan Turing",
        "role": "lecturer"
    })
    assert res.status_code == 201
    lec_token = (await client.post("/api/v1/auth/login", json={
        "email": lec_email,
        "password": "Password123!"
    })).json()["access_token"]
    lec_auth = {"Authorization": f"Bearer {lec_token}"}

    # 2. Register and login student
    stu_email = f"ada_{suffix}@socratica.edu"
    res = await client.post("/api/v1/auth/register", json={
        "email": stu_email,
        "password": "Password123!",
        "display_name": "Ada Lovelace",
        "role": "student"
    })
    assert res.status_code == 201
    stu_token = (await client.post("/api/v1/auth/login", json={
        "email": stu_email,
        "password": "Password123!"
    })).json()["access_token"]
    stu_auth = {"Authorization": f"Bearer {stu_token}"}

    # 3. Lecturer creates Course
    course_res = await client.post("/api/v1/courses", json={
        "code": f"CS301_{suffix}",
        "name": "Artificial Intelligence & Ethics",
        "description": "Core course on AI principles."
    }, headers=lec_auth)
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # 4. Lecturer enrolls student
    student_id = (await client.get("/api/v1/auth/me", headers=stu_auth)).json()["id"]
    enroll_res = await client.post(f"/api/v1/courses/{course_id}/enroll", json={
        "user_id": student_id,
        "course_role": "student"
    }, headers=lec_auth)
    assert enroll_res.status_code == 201

    # 5. Lecturer uploads a lecture document
    doc_content = b"""Mata Kuliah: Kecerdasan Buatan (CS301)
Dosen: Prof. Alan Turing
Silabus Pertemuan 1:
Topik: Pengantar Algoritma Pencarian.
Ujian Tengah Semester diadakan pada minggu ke-8.
Komponen Penilaian: Tugas 30%, UTS 30%, UAS 40%.
Ketentuan Keterlambatan: Pengurangan 10% per hari keterlambatan."""

    files = {
        "file": ("silabus_cs301.txt", doc_content, "text/plain")
    }
    data = {
        "document_name": "Silabus CS301 Lengkap",
        "document_type": "syllabus",
        "meeting": "1",
        "chapter": "Pendahuluan"
    }

    upload_res = await client.post(
        f"/api/v1/courses/{course_id}/documents",
        data=data,
        files=files,
        headers=lec_auth
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["document_name"] == "Silabus CS301 Lengkap"
    assert doc_data["course_id"] == course_id
    doc_id = doc_data["id"]

    # 6. Verify document appears in course document list for both lecturer & student
    docs_res = await client.get(f"/api/v1/courses/{course_id}/documents", headers=stu_auth)
    assert docs_res.status_code == 200
    docs_list = docs_res.json()
    assert any(d["id"] == doc_id for d in docs_list)

    # 7. Student creates a conversation in QA mode
    conv_res = await client.post("/api/v1/conversations", json={
        "course_id": course_id,
        "mode": "qa",
        "title": "Tanya Silabus & Penilaian"
    }, headers=stu_auth)
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 8. Student sends a question
    msg_res = await client.post(f"/api/v1/conversations/{conv_id}/messages", json={
        "content": "Berapa bobot penilaian untuk Tugas dan UTS pada mata kuliah ini?"
    }, headers=stu_auth)
    assert msg_res.status_code == 200
    reply = msg_res.json()
    assert reply["conversation_id"] == conv_id
    assert "content" in reply
    assert reply["status"] in ("answered", "insufficient_context", "error")

    # 9. Verify conversation and messages are stored in DB
    get_conv_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=stu_auth)
    assert get_conv_res.status_code == 200
    conv_data = get_conv_res.json()
    assert len(conv_data["messages"]) >= 2  # user message + assistant reply

    # 10. Check Escalation: if status was insufficient_context or error, escalation must exist
    if reply["status"] in ("insufficient_context", "error"):
        assert reply["escalation_id"] is not None
        esc_id = reply["escalation_id"]

        # Student can see escalation in own list
        my_esc = await client.get("/api/v1/escalations", headers=stu_auth)
        assert my_esc.status_code == 200
        assert any(e["id"] == esc_id for e in my_esc.json())

        # Lecturer can see escalation in course escalations
        course_esc = await client.get(f"/api/v1/escalations/course/{course_id}", headers=lec_auth)
        assert course_esc.status_code == 200
        assert any(e["id"] == esc_id for e in course_esc.json())

        # Lecturer resolves escalation
        resolve_res = await client.patch(f"/api/v1/escalations/{esc_id}", json={
            "status": "resolved",
            "resolution_note": "Bobot tugas 30%, UTS 30%, UAS 40%."
        }, headers=lec_auth)
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "resolved"
