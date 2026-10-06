"""
Security utilities — password hashing and JWT tokens.

Password hashing: Argon2id via passlib (industry-recommended, memory-hard).
JWT: python-jose with HS256.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Argon2id is recommended by OWASP for password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────


def _secret() -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured. Set it in your .env file.")
    return settings.jwt_secret


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    exp_delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_expire_minutes)
    )
    expire = datetime.now(UTC) + exp_delta
    payload["exp"] = expire
    payload["type"] = "access"
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    payload["type"] = "refresh"
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises JWTError on invalid/expired tokens.
    """
    return jwt.decode(token, _secret(), algorithms=[settings.jwt_algorithm])


def decode_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload
