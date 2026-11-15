from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, field_validator
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

from database import get_db
from config import get_settings
from limiter import limiter
from services.email_service import email_configured, send_password_reset_email

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
AUTH_COOKIE = "sl_token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _bearer_from_header(request: Request) -> str | None:
    value = request.headers.get("authorization") or ""
    scheme, _, param = value.partition(" ")
    if scheme.lower() == "bearer" and param.strip():
        return param.strip()
    return None


class BearerOrCookieScheme(OAuth2PasswordBearer):
    """Credential = `Authorization: Bearer` header first, then the HttpOnly sl_token cookie.
    No credential at all -> 401."""

    def __init__(self):
        super().__init__(tokenUrl="/api/v1/auth/login", auto_error=False)

    async def __call__(self, request: Request) -> str:  # type: ignore[override]
        token = _bearer_from_header(request) or request.cookies.get(AUTH_COOKIE)
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token


oauth2_scheme = BearerOrCookieScheme()


def _origin_allowed(origin: str) -> bool:
    origin = origin.strip().rstrip("/")
    if origin in {o.rstrip("/") for o in settings.origins_list if o}:
        return True
    if not settings.is_production:
        import re
        return bool(re.fullmatch(r"https?://(localhost|127\.0\.0\.1)(:\d+)?", origin))
    return False


def enforce_cookie_csrf(request: Request) -> None:
    """CSRF defence for cookie-authenticated state-changing requests: the browser-supplied
    Origin (or Referer) must be an allowed frontend origin. Requests authenticated with an
    Authorization Bearer header are not cookie-ambient and are exempt."""
    if request.method.upper() not in _UNSAFE_METHODS:
        return
    if _bearer_from_header(request):
        return
    origin = request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            from urllib.parse import urlparse
            p = urlparse(referer)
            origin = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else None
    if not origin or not _origin_allowed(origin):
        raise HTTPException(status_code=403, detail="Cross-origin request blocked.")


def validate_password_strength(v: str) -> str:
    """Shared password rule (registration and password reset). Raises ValueError."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes (bcrypt limit).")
    return v


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 120:
            raise ValueError("Name is required (max 120 characters).")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


class TokenResponse(BaseModel):
    user: UserOut
    # DEPRECATED: only populated when AUTH_RETURN_BODY_TOKEN=true. The credential is the
    # HttpOnly `sl_token` cookie.
    access_token: str | None = None
    token_type: str | None = None


def build_token_response(user: UserOut, token: str) -> TokenResponse:
    if settings.auth_return_body_token:
        return TokenResponse(user=user, access_token=token, token_type="bearer")
    return TokenResponse(user=user)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit - truncate to be safe
    truncated = password[:72]
    return pwd_context.hash(truncated)


def verify_password(plain: str, hashed: str) -> bool:
    # Bcrypt has a 72-byte limit - truncate to match hashing behavior
    truncated = plain[:72]
    return pwd_context.verify(truncated, hashed)


def create_access_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "tv": int(token_version or 0), "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _rows_affected(result) -> int:
    """Affected-row count from an execute() result: asyncpg status string ("UPDATE 1")
    or the SQLite wrapper's equivalent. Unknown/unparseable -> 0 (fail closed)."""
    try:
        return int(str(result).rsplit(" ", 1)[-1])
    except (TypeError, ValueError):
        return 0


_DUMMY_HASH: str | None = None


def _dummy_verify(password: str) -> None:
    """Burn a bcrypt verification so unknown-email logins take about as long as real ones."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = pwd_context.hash("dummy-password-for-timing")
    try:
        pwd_context.verify(password[:72], _DUMMY_HASH)
    except Exception:
        pass


async def _resolve_user(auth_token: str, db) -> dict:
    """Validate a JWT (signature, user exists, token_version) and return the user dict."""
    try:
        payload = jwt.decode(auth_token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Session revocation check
    token_tv = int(payload.get("tv", 0) or 0)
    current_tv = int(dict(user).get("token_version", 0) or 0)
    if token_tv != current_tv:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")

    return dict(user)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    # Credential: Bearer header first, else HttpOnly cookie (401 when neither is present).
    user = await _resolve_user(token, db)
    # Cookie-only (browser ambient) credentials need an Origin/Referer check on unsafe methods.
    enforce_cookie_csrf(request)
    return user


async def require_admin(current_user=Depends(get_current_user)):
    """Allow only users whose email is listed in ADMIN_EMAILS (comma-separated). Empty list = nobody."""
    allowed = {e.strip().lower() for e in (settings.admin_emails or "").split(",") if e.strip()}
    if (current_user.get("email") or "").lower() not in allowed:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return current_user


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        AUTH_COOKIE, path="/", httponly=True, samesite="lax", secure=settings.is_production
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/hour")
async def register(request: Request, data: RegisterRequest, response: Response, db=Depends(get_db)):
    email = data.email.lower().strip()
    existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    await db.execute(
        "INSERT INTO users (id, name, email, password, created_at) VALUES ($1, $2, $3, $4, $5)",
        user_id, data.name.strip(), email, hash_password(data.password), now,
    )

    token = create_access_token(user_id, 0)
    _set_auth_cookie(response, token)
    return build_token_response(
        UserOut(id=user_id, name=data.name.strip(), email=email, created_at=now), token
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    email = form.username.lower().strip()
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)

    if not user or not user["password"]:
        _dummy_verify(form.password)  # equalise timing with the real-password path
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        password_ok = verify_password(form.password, user["password"])
    except Exception:  # malformed/unknown hash must never become a 500 or a bypass
        password_ok = False
    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], dict(user).get("token_version", 0))
    _set_auth_cookie(response, token)
    return build_token_response(
        UserOut(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"]), token
    )


@router.post("/logout")
async def logout(request: Request, response: Response, db=Depends(get_db)):
    """Revoke the presented session (bumps token_version) and clear the HttpOnly cookie.
    Always succeeds; an invalid/missing credential just clears the cookie."""
    enforce_cookie_csrf(request)
    token = _bearer_from_header(request) or request.cookies.get(AUTH_COOKIE)
    if token:
        try:
            user = await _resolve_user(token, db)
            await db.execute(
                "UPDATE users SET token_version = COALESCE(token_version, 0) + 1 WHERE id = $1",
                user["id"],
            )
        except HTTPException:
            pass
    _clear_auth_cookie(response)
    return {"message": "Successfully logged out"}



@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(id=current_user["id"], name=current_user["name"], email=current_user["email"], created_at=current_user["created_at"])


# ─── Session revocation ──────────────────────────────────────────────────────

@router.post("/logout-all")
async def logout_all(response: Response, current_user=Depends(get_current_user), db=Depends(get_db)):
    """Revoke every existing session for this user by bumping their token_version."""
    await db.execute(
        "UPDATE users SET token_version = COALESCE(token_version, 0) + 1 WHERE id = $1",
        current_user["id"],
    )
    _clear_auth_cookie(response)
    return {"message": "All sessions have been signed out. Please sign in again."}


# ─── Password reset ──────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
@limiter.limit("5/hour")
async def forgot_password(request: Request, data: ForgotPasswordRequest,
                          background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Begin a password reset. Always returns the same message (never reveals whether
    an email is registered). A single-use, time-limited token is stored hashed.

    NOTE: no email provider is wired up yet — the token is logged server-side, and
    returned in the response ONLY in non-production so the flow can be tested.
    """
    email = data.email.lower().strip()
    generic = {"message": "If an account exists for that email, a password reset link has been sent."}

    user = await db.fetchrow("SELECT id FROM users WHERE email = $1 AND password != ''", email)
    if not user:
        return generic

    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(minutes=settings.reset_token_expire_minutes)).isoformat()
    now = datetime.utcnow().isoformat()
    # Only the newest link may work: invalidate this user's older unused tokens.
    await db.execute(
        "UPDATE password_resets SET used = 1 WHERE user_id = $1 AND used = 0", user["id"]
    )
    await db.execute(
        "INSERT INTO password_resets (id, user_id, token_hash, expires_at, used, created_at) "
        "VALUES ($1, $2, $3, $4, 0, $5)",
        str(uuid.uuid4()), user["id"], _hash_token(token), expires, now,
    )
    # Email configured: send in the background (response time must not reveal account
    # existence) and never expose the token in the response.
    if email_configured():
        background_tasks.add_task(
            send_password_reset_email, email, token, settings.reset_token_expire_minutes
        )
        return generic
    # No email provider: expose/log the token ONLY in an explicit development environment AND
    # when EXPOSE_RESET_TOKEN_IN_RESPONSE=true — a reset token in responses/logs would let
    # anyone with access take over accounts.
    if settings.is_development and settings.expose_reset_token_in_response:
        print(f"[auth] Password reset token for {email}: {token} (expires {expires})")
        return {**generic, "reset_token": token, "expires_at": expires}
    return generic


@router.post("/reset-password")
@limiter.limit("10/hour")
async def reset_password(request: Request, data: ResetPasswordRequest, db=Depends(get_db)):
    """Complete a password reset: set the new password and revoke all old sessions."""
    try:
        validate_password_strength(data.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    row = await db.fetchrow(
        "SELECT id, user_id, expires_at, used FROM password_resets WHERE token_hash = $1",
        _hash_token(data.token),
    )
    if not row or int(row["used"]) == 1:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has already been used.")

    expires = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else datetime.utcnow()
    if datetime.utcnow() > expires:
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    # Atomically consume the token first: only one concurrent request can flip used 0 -> 1.
    consumed = await db.execute(
        "UPDATE password_resets SET used = 1 WHERE id = $1 AND used = 0", row["id"]
    )
    if _rows_affected(consumed) != 1:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has already been used.")

    # Update password and bump token_version (revoke all sessions).
    await db.execute(
        "UPDATE users SET password = $1, token_version = COALESCE(token_version, 0) + 1 WHERE id = $2",
        hash_password(data.new_password), row["user_id"],
    )
    return {"message": "Your password has been reset. Please sign in with your new password."}
