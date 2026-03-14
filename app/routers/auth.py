"""Auth routes — token generation for API access."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    user_id: str
    role: str = "user"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Generate access token",
    description="Generate a JWT access token for API authentication.",
)
def generate_token(body: TokenRequest):
    token = create_access_token(body.user_id, body.role)
    return TokenResponse(access_token=token)
