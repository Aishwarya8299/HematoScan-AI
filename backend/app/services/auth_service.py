"""Authentication operations backed by MongoDB."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.collections import REVOKED_TOKENS_COLLECTION, USERS_COLLECTION
from app.schemas.auth import TokenResponse, TokenPayload, UserPublic, UserRole


async def authenticate_user(
    database: AsyncIOMotorDatabase[Any],
    email: str,
    password: str,
) -> dict[str, Any]:
    """Find an active user and verify the supplied password."""
    user = await database[USERS_COLLECTION].find_one(
        {"email": email.strip().lower(), "is_active": True}
    )
    if user is None or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def to_public_user(user: dict[str, Any]) -> UserPublic:
    """Map a MongoDB user document to a safe API response."""
    return UserPublic(
        id=str(user["_id"]),
        email=user["email"],
        role=UserRole(user["role"]),
        display_name=user["display_name"],
    )


def issue_token(user: dict[str, Any], settings: Settings) -> TokenResponse:
    """Issue a JWT for a validated user and include its expiry duration."""
    expires_in = settings.jwt_access_token_expire_minutes * 60
    token = create_access_token(
        subject=str(user["_id"]),
        role=UserRole(user["role"]),
        settings=settings,
        expires_delta=timedelta(seconds=expires_in),
    )
    return TokenResponse(access_token=token, expires_in=expires_in)


async def revoke_token(
    database: AsyncIOMotorDatabase[Any],
    token_payload: TokenPayload,
    expires_at: datetime,
) -> None:
    """Store a token revocation marker until the token would naturally expire."""
    await database[REVOKED_TOKENS_COLLECTION].update_one(
        {"token_id": token_payload.token_id},
        {
            "$set": {
            "token_id": token_payload.token_id,
                "revoked_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
            }
        },
        upsert=True,
    )


def new_user_document(
    email: str,
    password_hash: str,
    role: UserRole,
    display_name: str,
) -> dict[str, Any]:
    """Build a normalized user document for seed scripts and future admin flows."""
    return {
        "_id": uuid4().hex,
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "role": role.value,
        "display_name": display_name.strip(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }


async def register_user(
    database: AsyncIOMotorDatabase[Any],
    email: str,
    password: str,
    display_name: str,
    role: UserRole,
) -> dict[str, Any]:
    """Create a professional account when the email is not already registered."""
    normalized_email = email.strip().lower()
    existing = await database[USERS_COLLECTION].find_one({"email": normalized_email})
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = new_user_document(
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
        display_name=display_name,
    )
    await database[USERS_COLLECTION].insert_one(user)
    return user
