"""Password, JWT, and role authorization primitives."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings
from app.schemas.auth import TokenPayload, UserRole

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    """Hash a plaintext password with the configured adaptive algorithm."""
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compare a plaintext password with a stored hash."""
    return password_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    role: UserRole,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT containing the minimum authorization claims."""
    lifetime = expires_delta or timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    expires_at = datetime.now(timezone.utc) + lifetime
    payload = {
        "sub": subject,
        "role": role.value,
        "jti": uuid4().hex,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    """Verify a JWT and return validated claims or a 401 error."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return TokenPayload.model_validate(payload)
    except (JWTError, ValueError):
        raise credentials_error from None


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPayload:
    """FastAPI dependency that validates the current bearer token."""
    token_payload = decode_access_token(token, settings)
    database = getattr(request.app.state, "database", None)
    if database is not None:
        revoked = await database["revoked_tokens"].find_one(
            {"token_id": token_payload.token_id}
        )
        if revoked is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return token_payload


def require_role(*allowed_roles: UserRole) -> Callable[..., TokenPayload]:
    """Build a dependency that permits only the supplied user roles."""

    async def role_guard(
        current_user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_guard
