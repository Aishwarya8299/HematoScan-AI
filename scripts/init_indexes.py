"""Create Hematoscan MongoDB indexes for an existing environment."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.db.mongodb import close_mongodb, connect_mongodb, ensure_indexes, get_database


async def main() -> None:
    """Connect, create indexes, and close the client."""
    settings = get_settings()
    client = await connect_mongodb(settings)
    if client is None:
        raise RuntimeError("MongoDB is unavailable; indexes were not initialized")

    try:
        await ensure_indexes(get_database(client, settings))
    finally:
        await close_mongodb(client)


if __name__ == "__main__":
    asyncio.run(main())