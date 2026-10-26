"""Authentication and session endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.core.config import Settings, get_settings
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import (
    authenticate_user,
    issue_token,
    register_user,
    revoke_token,
    to_public_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(credentials: RegisterRequest, database: Database) -> UserPublic:
    """Create a technician or doctor account and return its public profile."""
    user = await register_user(
        database,
        credentials.email,
        credentials.password,
        credentials.display_name,
        credentials.role,
    )
    return to_public_user(user)


@router.post("/login", response_model=TokenResponse, summary="Create a login session")
async def login(
    credentials: LoginRequest,
    database: Database,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Validate credentials and return a signed bearer token."""
    user = await authenticate_user(database, credentials.email, credentials.password)
    return issue_token(user, settings)


@router.get("/me", response_model=UserPublic, summary="Get the current user")
async def me(current_user: CurrentUser, database: Database) -> UserPublic:
    """Return the authenticated user's profile."""
    user = await database["users"].find_one({"_id": current_user.subject})
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return to_public_user(user)


@router.post("/logout", response_model=MessageResponse, summary="Revoke the current session")
async def logout(
    current_user: CurrentUser,
    database: Database,
) -> MessageResponse:
    """Revoke only the bearer token supplied for this request."""
    await revoke_token(database, current_user, current_user.expires_at)
    return MessageResponse(message="Logged out successfully")
