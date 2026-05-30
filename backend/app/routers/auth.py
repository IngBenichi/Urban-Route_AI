from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.dependencies import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if body.username != settings.ADMIN_USERNAME or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = create_access_token({"sub": body.username})
    return TokenResponse(access_token=token)
