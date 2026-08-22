from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
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


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db=Depends(get_db)):
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

    token = create_access_token(user_id)
    return TokenResponse(
        user=UserOut(id=user_id, name=data.name.strip(), email=email, created_at=now),
        access_token=token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    email = form.username.lower().strip()
    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)

    if not user or not user["password"] or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"])
    return TokenResponse(
        user=UserOut(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"]),
        access_token=token,
    )


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(**current_user)
