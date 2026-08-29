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

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from datetime import datetime
import uuid
import httpx
import json

from database import get_db
from config import get_settings
from routers.auth import create_access_token, UserOut, TokenResponse, _set_auth_cookie

router = APIRouter()
settings = get_settings()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleTokenRequest(BaseModel):
    credential: str  # Google ID token (JWT from Google)


@router.post("/google", response_model=TokenResponse, status_code=200)
async def google_signin(data: GoogleTokenRequest, response: Response, db=Depends(get_db)):
    """
    Verify Google ID token and sign the user in / create account.
    Frontend sends the credential from Google Identity Services.
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
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            payload = resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to verify token with Google")

    # Validate audience
    if payload.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=401, detail="Google token was not issued for this client")

    # Validate issuer
    if payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    email = payload.get("email", "").lower().strip()
    name = payload.get("name", "").strip() or email.split("@")[0]

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email address")

    user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
    now = datetime.utcnow().isoformat()

    if user:
        user_id = user["id"]
        user_name = user["name"]
        created_at = user["created_at"]
        token_version = dict(user).get("token_version", 0)
    else:
        user_id = str(uuid.uuid4())
        user_name = name
        created_at = now
        token_version = 0
        await db.execute(
            "INSERT INTO users (id, name, email, password, created_at) VALUES ($1, $2, $3, $4, $5)",
            user_id, name, email, "", now,
        )

    token = create_access_token(user_id, token_version)
    _set_auth_cookie(response, token)
    return TokenResponse(
        user=UserOut(id=user_id, name=user_name, email=email, created_at=created_at),
        access_token=token,
    )