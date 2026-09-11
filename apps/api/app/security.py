"""Minimal JWT-style API security primitives for WO-2026-002.

This module is intentionally dependency-light. Production deployment should
provide JWT verification through a trusted identity provider and set
MOUSAVITAX_API_TOKEN / MOUSAVITAX_ADMIN_TOKEN via environment secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str


def _configured_tokens() -> dict[str, Principal]:
    result: dict[str, Principal] = {}
    user_token = os.getenv("MOUSAVITAX_API_TOKEN", "").strip()
    admin_token = os.getenv("MOUSAVITAX_ADMIN_TOKEN", "").strip()
    if user_token:
        result[user_token] = Principal(user_id="api-user", role="taxpayer")
    if admin_token:
        result[admin_token] = Principal(user_id="admin", role="admin")
    return result


async def require_principal(authorization: Optional[str] = Header(default=None)) -> Principal:
    """Authenticate a request using configured bearer tokens.

    This is a transitional hardening layer for the current MVP. The tokens are
    supplied only through environment secrets and are never persisted.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:].strip()
    principal = _configured_tokens().get(token)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal


def require_role(principal: Principal, *roles: str) -> Principal:
    if principal.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return principal
