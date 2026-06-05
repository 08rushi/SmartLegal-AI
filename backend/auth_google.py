"""
Google OAuth 2.0 sign-in endpoint.
Accepts a Google ID token from the frontend, verifies it,
creates/updates the user, and returns a SmartLegal JWT.

Security:
- Verifies token signature with Google's public key
- Validates audience (aud claim) matches the app's Client ID
- Validates expiration (exp claim)
- Validates issuer (iss claim) is Google
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
import uuid
import httpx
import json

from database import get_db
from config import get_settings
from routers.auth import create_access_token, UserOut, TokenResponse

router = APIRouter()
settings = get_settings()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleTokenRequest(BaseModel):
    credential: str  # Google ID token (JWT from Google)


@router.post("/google", response_model=TokenResponse, status_code=200)
async def google_signin(data: GoogleTokenRequest, db=Depends(get_db)):
    """
    Verify Google ID token and sign the user in / create account.
    Frontend sends the credential from Google Identity Services.

    Validates:
    1. Token signature with Google
    2. Token audience matches our Client ID (GOOGLE_CLIENT_ID)
    3. Token is not expired
    4. Issuer is Google
    """

    if not settings.google_client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Contact support."
        )

    # Verify token with Google
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                GOOGLE_TOKEN_INFO_URL,
                params={"id_token": data.credential},
                timeout=5.0,
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail="Google service temporarily unavailable"
            )

    if resp.status_code != 200:
        error_detail = "Invalid or expired Google token"
        try:
            error_data = resp.json()
            if "error_description" in error_data:
                error_detail = error_data["error_description"]
        except:
            pass
        raise HTTPException(status_code=401, detail=error_detail)

    google_data = resp.json()

    # 1. Validate audience claim (CRITICAL: must match our Client ID)
    token_aud = google_data.get("aud")
    if not token_aud or token_aud != settings.google_client_id:
        raise HTTPException(
            status_code=401,
            detail="Token audience mismatch. Token not intended for this app."
        )

    # 2. Validate issuer is Google
    token_iss = google_data.get("iss")
    if token_iss not in ("https://accounts.google.com", "accounts.google.com"):
        raise HTTPException(
            status_code=401,
            detail="Invalid token issuer"
        )

    # 3. Extract and validate email
    email = google_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token")

    # 4. Verify email is verified by Google
    email_verified = google_data.get("email_verified", False)
    if not email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified by Google. Please verify your email first."
        )

    name = google_data.get("name", email.split("@")[0])  # fallback to email prefix

    # Check if user exists
    async with db.execute("SELECT * FROM users WHERE email = ?", (email,)) as cur:
        user = await cur.fetchone()

    now = datetime.utcnow().isoformat()

    if user:
        # User exists: return without modification (preserves their existing data)
        user_id = user["id"]
        user_name = user["name"]
        created_at = user["created_at"]
    else:
        # Create new user (no password for Google OAuth users)
        user_id = str(uuid.uuid4())
        user_name = name
        created_at = now
        await db.execute(
            "INSERT INTO users (id, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, "", now),
        )
        await db.commit()

    token = create_access_token(user_id)
    return TokenResponse(
        user=UserOut(id=user_id, name=user_name, email=email, created_at=created_at),
        access_token=token,
    )