"""Seed development-only technician and doctor accounts."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.collections import USERS_COLLECTION
from app.db.mongodb import close_mongodb, connect_mongodb, get_database
from app.schemas.auth import UserRole
from app.services.auth_service import new_user_document


SEED_USERS = (
    ("technician@hematoscan.local", "Technician", UserRole.TECHNICIAN),
    ("doctor@hematoscan.local", "Doctor", UserRole.DOCTOR),
)
DEFAULT_PASSWORD = "ChangeMe123!"


async def main() -> None:
    """Create or update development accounts without duplicating users."""
    settings = get_settings()
    client = await connect_mongodb(settings)
    if client is None:
        raise RuntimeError("MongoDB is unavailable; users were not seeded")

    database = get_database(client, settings)
    assert database is not None
    try:
        for email, display_name, role in SEED_USERS:
            document = new_user_document(
                email=email,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=role,
                display_name=display_name,
            )
            await database[USERS_COLLECTION].update_one(
                {"email": document["email"]},
                {"$setOnInsert": document},
                upsert=True,
            )
            print(f"Seeded account: {email} ({role.value})")
    finally:
        await close_mongodb(client)


if __name__ == "__main__":
    asyncio.run(main())