"""
Google OAuth 2.0 sign-in endpoint.
Accepts a Google ID token from the frontend, verifies it,
creates/updates the user, and returns a SmartLegal JWT.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import httpx

from database import get_db
from routers.auth import create_access_token, UserOut, TokenResponse

router = APIRouter()

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleTokenRequest(BaseModel):
    credential: str  # Google ID token (JWT from Google)


@router.post("/google", response_model=TokenResponse)
async def google_signin(data: GoogleTokenRequest, db=Depends(get_db)):
    """
    Verify Google ID token and sign the user in / create account.
    Frontend sends the credential from Google Identity Services.
    """
    # Verify token with Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": data.credential},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_data = resp.json()

    # Validate token audience (optional but recommended)
    email = google_data.get("email")
    name = google_data.get("name", email)
    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token")

    # Check if user exists
    async with db.execute("SELECT * FROM users WHERE email = ?", (email,)) as cur:
        user = await cur.fetchone()

    now = datetime.utcnow().isoformat()

    if user:
        user_id = user["id"]
        user_name = user["name"]
        created_at = user["created_at"]
    else:
        # Create new user (no password for Google users)
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