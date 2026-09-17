# api/lib/session_guard.py
from lib.auth import verify_session_jwt, get_bearer_token


def require_user(headers) -> dict:
    """Extract and verify the session JWT from headers.
    Returns a user dict or raises PermissionError.
    """
    token = get_bearer_token(headers)
    if not token:
        raise PermissionError("missing_token")
    payload = verify_session_jwt(token)
    if not payload:
        raise PermissionError("invalid_token")
    return {
        "id":     int(payload["sub"]),
        "email":  payload["email"],
        "agency": payload["agency"],
        "role":   payload["role"],
    }