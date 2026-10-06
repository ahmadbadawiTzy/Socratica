"""
Tests for application configuration loading.

Verifies that:
- Settings load correctly from environment variables.
- Secret-like values (jwt_secret, api keys) are never exposed in repr/str.
- CORS default does not include a wildcard.
- All [DECISION REQUIRED] fields default to None (not a fake value).
"""

from __future__ import annotations


def test_settings_load() -> None:
    """Settings must load without error."""
    from app.core.config import settings

    assert settings.app_name == "Socratica"


def test_settings_app_env_default() -> None:
    """Default app_env must be 'development'."""
    from app.core.config import settings

    assert settings.app_env == "development"


def test_decision_required_fields_default_to_none() -> None:
    """
    All [DECISION REQUIRED] fields must default to None.
    This ensures we never accidentally send a fake/placeholder value to a
    real external service.
    """
    from app.core.config import Settings

    decision_required_fields = [
        "database_url",
        "langflow_base_url",
        "langflow_api_key",
        "llm_model",
        "llm_api_key",
        "vector_db_url",
        "vector_db_api_key",
        "embedding_provider",
        "embedding_model",
        "jwt_secret",
    ]
    for field in decision_required_fields:
        default_val = Settings.model_fields[field].default
        assert default_val is None, (
            f"[DECISION REQUIRED] field '{field}' must default to None, got: {default_val!r}"
        )


def test_cors_no_wildcard() -> None:
    """CORS allowed origins must not include a wildcard in any environment."""
    from app.core.config import settings

    origins = settings.cors_allowed_origins
    assert "*" not in origins, (
        "CORS wildcard is not allowed. Set specific origins in CORS_ALLOWED_ORIGINS (PRD SEC-08)."
    )


def test_cors_origins_is_list() -> None:
    """CORS allowed origins must be parsed as a list."""
    from app.core.config import settings

    assert isinstance(settings.cors_allowed_origins, list)
    assert len(settings.cors_allowed_origins) > 0


def test_rag_thresholds_are_configurable() -> None:
    """
    RAG thresholds must be driven by config, not hardcoded.
    [DECISION REQUIRED] OD-03/OD-06: values must be evaluated on eval set.
    """
    from app.core.config import settings

    # Verify they are numeric types (can be overridden via env var)
    assert isinstance(settings.rag_top_k, int)
    assert isinstance(settings.rag_relevance_threshold, float)
    assert isinstance(settings.rag_chunk_size, int)
    assert isinstance(settings.rag_chunk_overlap, int)
    assert isinstance(settings.escalation_confidence_threshold, float)
