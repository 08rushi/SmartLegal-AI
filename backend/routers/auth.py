from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

from database import get_db
from config import get_settings

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: str


class TokenResponse(BaseModel):
    user: UserOut
    access_token: str
    token_type: str = "bearer"


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


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    # Extract token from Authorization header or HttpOnly cookie
    auth_token = token
    if not auth_token and request:
        auth_token = request.cookies.get("sl_token")

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")

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


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="sl_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, response: Response, db=Depends(get_db)):
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
    return TokenResponse(
        user=UserOut(id=user_id, name=data.name.strip(), email=email, created_at=now),
        access_token=token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    email = form.username.lower().strip()
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)

    if not user or not user["password"] or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], dict(user).get("token_version", 0))
    _set_auth_cookie(response, token)
    return TokenResponse(
        user=UserOut(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"]),
        access_token=token,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear HttpOnly authentication cookie."""
    response.delete_cookie("sl_token")
    return {"message": "Successfully logged out"}



@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(id=current_user["id"], name=current_user["name"], email=current_user["email"], created_at=current_user["created_at"])


# ─── Session revocation ──────────────────────────────────────────────────────

@router.post("/logout-all")
async def logout_all(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Revoke every existing session for this user by bumping their token_version."""
    await db.execute(
        "UPDATE users SET token_version = COALESCE(token_version, 0) + 1 WHERE id = $1",
        current_user["id"],
    )
    return {"message": "All sessions have been signed out. Please sign in again."}


# ─── Password reset ──────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db=Depends(get_db)):
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
    await db.execute(
        "INSERT INTO password_resets (id, user_id, token_hash, expires_at, used, created_at) "
        "VALUES ($1, $2, $3, $4, 0, $5)",
        str(uuid.uuid4()), user["id"], _hash_token(token), expires, now,
    )
    print(f"[auth] Password reset token for {email}: {token} (expires {expires})")

    if not settings.is_production:
        return {**generic, "reset_token": token, "expires_at": expires}
    return generic


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db=Depends(get_db)):
    """Complete a password reset: set the new password and revoke all old sessions."""
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    row = await db.fetchrow(
        "SELECT id, user_id, expires_at, used FROM password_resets WHERE token_hash = $1",
        _hash_token(data.token),
    )
    if not row or int(row["used"]) == 1:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has already been used.")

    expires = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else datetime.utcnow()
    if datetime.utcnow() > expires:
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    # Update password, mark token used, and bump token_version (revoke all sessions).
    await db.execute(
        "UPDATE users SET password = $1, token_version = COALESCE(token_version, 0) + 1 WHERE id = $2",
        hash_password(data.new_password), row["user_id"],
    )
    await db.execute("UPDATE password_resets SET used = 1 WHERE id = $1", row["id"])
    return {"message": "Your password has been reset. Please sign in with your new password."}
