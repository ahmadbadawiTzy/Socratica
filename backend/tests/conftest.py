"""Test configuration and shared fixtures for Socratica backend tests."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Return the configured FastAPI application instance."""
    from app.main import create_app

    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Return an async test client for the application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def cleanup_db():
    yield
    from app.db.session import engine
    if engine is not None:
        await engine.dispose()
