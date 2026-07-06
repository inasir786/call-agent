import secrets
from fastapi import APIRouter, HTTPException
from app.config.settings import settings
from app.schemas.schemas import LoginRequest, TokenResponse
from app.utils.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    valid_user = secrets.compare_digest(payload.username, settings.admin_username)
    valid_pass = secrets.compare_digest(payload.password, settings.admin_password)
    if not (valid_user and valid_pass):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(access_token=create_access_token(payload.username))
