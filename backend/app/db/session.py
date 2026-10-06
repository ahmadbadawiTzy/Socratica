"""
SQLAlchemy declarative base and async engine factory.

Database engine: [DECISION REQUIRED] OD-03
  Recommended: PostgreSQL with asyncpg driver.
  The DATABASE_URL environment variable controls the engine at runtime.
  Connection string format: postgresql+asyncpg://user:pass@host:port/dbname

  If a different RDBMS is needed, only this module and the Alembic env.py
  need to change — the models and repositories stay unchanged.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _get_engine() -> object:
    """
    Create the async SQLAlchemy engine.

    Returns a sentinel object if DATABASE_URL is not configured so that the
    application can start in development without a database (e.g. to serve
    the /health endpoint). Any DB-dependent endpoint will fail gracefully.
    """
    if not settings.database_url:
        logger.warning(
            "[DECISION REQUIRED] OD-03 — DATABASE_URL is not set. "
            "Database-dependent endpoints will not be available."
        )
        return None  # type: ignore[return-value]

    return create_async_engine(
        settings.database_url,
        echo=settings.app_debug,
        pool_pre_ping=True,
    )


engine = _get_engine()

# Session factory — used via dependency injection in API endpoints.
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = (
    async_sessionmaker(engine, expire_on_commit=False)  # type: ignore[arg-type]
    if engine is not None
    else None
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    Usage in endpoints:
        async def my_endpoint(db: AsyncSession = Depends(get_db_session)): ...
    """
    if AsyncSessionLocal is None:
        from app.core.errors import ServiceUnavailableError

        raise ServiceUnavailableError(
            "Database is not configured. Set DATABASE_URL in your environment."
        )
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
