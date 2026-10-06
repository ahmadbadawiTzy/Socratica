"""API v1 router — aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    courses,
    documents,
    escalations,
    health,
    langflow_health,
)

api_router = APIRouter(prefix="/api/v1")

# ── Public endpoints ──────────────────────────────────────────────────────────
api_router.include_router(health.router, tags=["health"])
api_router.include_router(langflow_health.router, tags=["health"])

# ── Auth ──────────────────────────────────────────────────────────────────────
api_router.include_router(auth.router, tags=["auth"])

# ── Authenticated endpoints ───────────────────────────────────────────────────
api_router.include_router(courses.router, tags=["courses"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(escalations.router, tags=["escalations"])
