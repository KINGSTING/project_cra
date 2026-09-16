# lib/auth.py
import os
import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET = os.environ.get("JWT_SECRET") or os.environ.get("TOKEN_SECRET")
JWT_ALG    = "HS256"
JWT_TTL_DAYS = 30


def mint_session_jwt(user: dict) -> str:
    """Sign a session JWT for the given user row (dict)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub":    str(user["id"]),
        "email":  user["email"],
        "agency": user["agency"],
        "role":   user["role"],
        "iat":    int(now.timestamp()),
        "exp":    int((now + timedelta(days=JWT_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def verify_session_jwt(token: str) -> dict | None:
    """Return the decoded payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


def get_bearer_token(headers) -> str | None:
    """Extract 'Bearer <token>' from an email.message.Message headers object."""
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth[len("Bearer "):].strip() or None