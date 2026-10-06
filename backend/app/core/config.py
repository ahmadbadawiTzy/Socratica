"""
Application configuration via environment variables.

All values that can change between environments MUST be sourced from env vars.
Never hardcode secrets, credentials, or environment-specific values.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "Socratica"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"  # noqa: S104
    app_port: int = 8000

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allowed_origins_raw: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("cors_allowed_origins_raw", mode="before")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins_raw.split(",") if o.strip()]

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str | None = None

    # ── Langflow ──────────────────────────────────────────────────────────────
    # Running in Docker (ibm-hacktiv8-langflow), port 7860, LANGFLOW_AUTO_LOGIN=true
    langflow_base_url: str | None = None
    langflow_api_key: str | None = None
    langflow_timeout_seconds: float = 30.0

    # Flow IDs — obtained after importing flows into Langflow
    langflow_unified_flow_id: str | None = None
    langflow_ingestion_flow_id: str | None = None
    langflow_retrieval_flow_id: str | None = None
    langflow_socratic_flow_id: str | None = None
    langflow_evaluator_flow_id: str | None = None
    langflow_guardrail_flow_id: str | None = None

    # ── LLM ───────────────────────────────────────────────────────────────────
    # Gemini is configured inside Langflow, not called directly from FastAPI.
    # [DECISION REQUIRED] OD-02 — provider set to gemini via Langflow
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None  # kept for future direct usage; Gemini key goes in Langflow

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "socratica"

    # ── Vector Database (generic alias) ───────────────────────────────────────
    vector_db_provider: str = "qdrant"
    vector_db_url: str | None = None
    vector_db_api_key: str | None = None

    # ── Embedding ─────────────────────────────────────────────────────────────
    # Gemini embedding model configured inside Langflow
    embedding_provider: str | None = None
    embedding_model: str | None = None

    # ── Authentication ────────────────────────────────────────────────────────
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # ── File Upload ───────────────────────────────────────────────────────────
    upload_max_size_mb: int = 50
    upload_allowed_extensions_raw: str = "pdf,docx,pptx,txt,md,py,js,ts,java,cpp,c"

    @property
    def upload_allowed_extensions(self) -> set[str]:
        return {
            e.strip().lower() for e in self.upload_allowed_extensions_raw.split(",") if e.strip()
        }

    upload_dir: str = "/tmp/socratica_uploads"  # noqa: S108

    # ── RAG Configuration ─────────────────────────────────────────────────────
    rag_top_k: int = 5
    rag_relevance_threshold: float = 0.70
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64

    # ── Escalation ────────────────────────────────────────────────────────────
    escalation_confidence_threshold: float = 0.70

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_chat: str = "30/minute"
    rate_limit_upload: str = "10/minute"
    rate_limit_auth: str = "10/minute"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Frontend ──────────────────────────────────────────────────────────────
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
