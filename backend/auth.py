from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "604800"))  # 7 days

def get_password_ok(password: str) -> bool:
    expected = os.getenv("MEALPLANNER_PASSWORD", "changeme")
    # Simple shared password for two-person use.
    return password == expected

def create_token(payload: Dict[str, Any]) -> str:
    now = int(time.time())
    claims = {
        **payload,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None
