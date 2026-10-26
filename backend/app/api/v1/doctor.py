"""Doctor queue, case detail, and review endpoints."""

from mimetypes import guess_type

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.api.deps import Database
from app.core.security import require_role
from app.schemas.auth import TokenPayload, UserRole
from app.core.config import Settings, get_settings
from app.schemas.case import CaseQueueItem, CaseRecord, CaseReviewUpdate
from app.services.case_service import (
    get_case,
    get_case_image_path,
    list_cases,
    review_case,
    to_case_record,
    to_queue_item,
)

router = APIRouter(prefix="/doctor", tags=["Doctor"])
DoctorUser = require_role(UserRole.DOCTOR)


@router.get("/queue", response_model=list[CaseQueueItem])
async def doctor_queue(
    database: Database,
    _: TokenPayload = Depends(DoctorUser),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[CaseQueueItem]:
    """Return awaiting-review cases with AI-flagged cases first."""
    cursor = (
        database["cases"]
        .find({"status": "awaiting_review"})
        .sort([("priority", -1), ("created_at", -1)])
        .limit(limit)
    )
    return [to_queue_item(document) async for document in cursor]


@router.get("/case/{case_id}", response_model=CaseRecord)
async def case_detail(
    case_id: str,
    database: Database,
    _: TokenPayload = Depends(DoctorUser),
) -> CaseRecord:
    """Return the full inference result and review state for one case."""
    return to_case_record(
        await get_case(database, case_id), f"/api/v1/doctor/case/{case_id}/image"
    )


@router.get("/cases", response_model=list[CaseRecord])
async def doctor_cases(
    database: Database,
    _: TokenPayload = Depends(DoctorUser),
    limit: int = Query(default=200, ge=1, le=300),
) -> list[CaseRecord]:
    """Return the complete case/report history for doctors."""
    cases = await list_cases(database, limit=limit)
    return [
        to_case_record(document, f"/api/v1/doctor/case/{document['_id']}/image")
        for document in cases
    ]


@router.get("/case/{case_id}/image")
async def doctor_case_image(
    case_id: str,
    database: Database,
    settings: Settings = Depends(get_settings),
    _: TokenPayload = Depends(DoctorUser),
) -> FileResponse:
    """Serve the original uploaded image to an authenticated doctor."""
    document = await get_case(database, case_id)
    path = get_case_image_path(document, settings)
    return FileResponse(path, media_type=guess_type(path.name)[0] or "application/octet-stream")


@router.patch("/case/{case_id}/review", response_model=CaseRecord)
async def update_case_review(
    case_id: str,
    review: CaseReviewUpdate,
    database: Database,
    doctor: TokenPayload = Depends(DoctorUser),
) -> CaseRecord:
    """Save doctor notes and optionally mark the case reviewed."""
    return to_case_record(
        await review_case(database, case_id, review, doctor.subject),
        f"/api/v1/doctor/case/{case_id}/image",
    )