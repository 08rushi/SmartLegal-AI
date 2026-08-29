from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.share_service import create_share_grant, get_share_grant, revoke_share_grant
from routers.auth import get_current_user

router = APIRouter()


class ShareCreateRequest(BaseModel):
    document_id: str
    expiration_hours: int = 72


@router.post("/create")
async def create_share_link(
    req: ShareCreateRequest,
    current_user=Depends(get_current_user),
):
    """Generate secure read-only share link for a document (SL-076)."""
    grant = create_share_grant(current_user["id"], req.document_id, req.expiration_hours)
    return {
        "message": "Share link generated successfully.",
        "share_token": grant["token"],
        "expires_at": grant["expires_at"],
        "share_url": f"/share/{grant['token']}",
    }


@router.get("/{token}")
async def access_shared_document(token: str):
    """Access shared document via share token (SL-076)."""
    grant = get_share_grant(token)
    if not grant:
        raise HTTPException(status_code=404, detail="Share link is invalid, expired, or revoked.")

    return {
        "status": "valid",
        "document_id": grant["document_id"],
        "permission": grant["permission"],
        "expires_at": grant["expires_at"],
    }


@router.post("/{token}/revoke")
async def revoke_share_link(
    token: str,
    current_user=Depends(get_current_user),
):
    """Revoke active share link (SL-076)."""
    success = revoke_share_grant(current_user["id"], token)
    if not success:
        raise HTTPException(status_code=403, detail="Unable to revoke share link.")
    return {"message": "Share link revoked successfully."}
