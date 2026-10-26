"""Async MongoDB client lifecycle helpers."""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings
from app.db.collections import INDEXES

logger = logging.getLogger("hematoscan.db.mongodb")


async def connect_mongodb(settings: Settings) -> AsyncIOMotorClient | None:
    """Create and verify a MongoDB client, returning None when unavailable."""
    client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
    )
    try:
        await client.admin.command("ping")
    except Exception as exc:
        logger.warning("MongoDB unavailable: %s", exc)
        client.close()
        return None

    logger.info("MongoDB connection established: %s", settings.mongodb_db_name)
    return client


def get_database(
    client: AsyncIOMotorClient | None, settings: Settings
) -> AsyncIOMotorDatabase[Any] | None:
    """Return the configured database when a client is connected."""
    return client[settings.mongodb_db_name] if client is not None else None


async def ensure_indexes(database: AsyncIOMotorDatabase[Any] | None) -> None:
    """Create required indexes without removing existing application data."""
    if database is None:
        return

    for collection_name, indexes in INDEXES.items():
        await database[collection_name].create_indexes(indexes)
        logger.info("MongoDB indexes ready: %s", collection_name)


async def close_mongodb(client: AsyncIOMotorClient | None) -> None:
    """Close the MongoDB client during application shutdown."""
    if client is not None:
        client.close()
        logger.info("MongoDB connection closed")
