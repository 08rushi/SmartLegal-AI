from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from jose import jwt, JWTError

def get_user_or_ip_key(request: Request) -> str:
    """
    Extract user ID from JWT token (Header or Cookie) for per-user rate limiting.
    Falls back to remote IP address for unauthenticated requests.
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.cookies and "sl_token" in request.cookies:
        token = request.cookies.get("sl_token")

    if token:
        try:
            from config import get_settings
            settings = get_settings()
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass

    return get_remote_address(request)


# Single shared limiter — keyed by user_id when signed in, remote IP address otherwise.
limiter = Limiter(key_func=get_user_or_ip_key)