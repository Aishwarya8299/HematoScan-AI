"""Shared FastAPI dependencies for database and authentication access."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import get_current_user
from app.schemas.auth import TokenPayload


def get_db(request: Request) -> AsyncIOMotorDatabase[Any]:
    """Return the connected database or report dependency unavailability."""
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )
    return database


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
Database = Annotated[AsyncIOMotorDatabase[Any], Depends(get_db)]
