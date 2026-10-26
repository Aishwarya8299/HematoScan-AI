"""Doctor-facing case queries and review updates."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings
from app.db.collections import CASES_COLLECTION
from app.schemas.case import CaseQueueItem, CaseRecord, CaseReviewUpdate


def _case_id(document: dict[str, Any]) -> str:
    """Normalize MongoDB/string identifiers for API responses."""
    return str(document["_id"])


def to_queue_item(document: dict[str, Any]) -> CaseQueueItem:
    """Map a stored case to its compact queue representation."""
    inference = document.get("inference", {})
    return CaseQueueItem(
        case_id=_case_id(document),
        patient_id=document["patient_id"],
        filename=document["filename"],
        status=document["status"],
        priority=document.get("priority", 0),
        predicted_class=inference.get("predicted_class"),
        classifier_confidence=inference.get("classifier_confidence"),
        created_at=document["created_at"],
    )


def to_case_record(
    document: dict[str, Any], image_url: str | None = None
) -> CaseRecord:
    """Map a stored case to its detailed API representation."""
    return CaseRecord.model_validate(
        {**document, "_id": _case_id(document), "image_url": image_url}
    )


async def get_case(
    database: AsyncIOMotorDatabase[Any], case_id: str
) -> dict[str, Any]:
    """Fetch a case or raise a consistent not-found response."""
    document = await database[CASES_COLLECTION].find_one({"_id": case_id})
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return document

async def list_cases(
    database: AsyncIOMotorDatabase[Any],
    created_by: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return persisted cases for technician history or doctor reports."""
    query = {"created_by": created_by} if created_by else {}
    cursor = database[CASES_COLLECTION].find(query).sort("created_at", -1).limit(limit)
    return [document async for document in cursor]

def get_case_image_path(document: dict[str, Any], settings: Settings) -> Path:
    """Resolve a stored case image while preventing path traversal."""
    stored_path = document.get("stored_path")
    if not stored_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case image not found")

    image_path = settings.resolve_path(Path(stored_path))
    upload_root = settings.resolve_path(settings.upload_dir)
    try:
        image_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case image not found") from None
    if not image_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case image not found")
    return image_path


async def review_case(
    database: AsyncIOMotorDatabase[Any],
    case_id: str,
    review: CaseReviewUpdate,
    doctor_id: str,
) -> dict[str, Any]:
    """Save doctor notes and optionally complete the review transition."""
    current = await get_case(database, case_id)
    update: dict[str, Any] = {
        "doctor_notes": review.notes,
        "reviewed_by": doctor_id,
        "reviewed_at": datetime.now(timezone.utc),
    }
    if review.mark_reviewed:
        update["status"] = "reviewed"
    await database[CASES_COLLECTION].update_one({"_id": case_id}, {"$set": update})
    return {**current, **update}