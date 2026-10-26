"""Technician image upload and gated inference endpoints."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from mimetypes import guess_type

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.api.deps import Database
from app.core.config import Settings, get_settings
from app.core.security import require_role
from app.schemas.auth import TokenPayload, UserRole
from app.schemas.case import CaseRecord, CaseUploadResponse
from app.services.case_service import get_case, get_case_image_path, list_cases, to_case_record
from app.services.inference_service import run_inference
from app.services.upload_service import save_image_upload

router = APIRouter(prefix="/technician", tags=["Technician"])
TechnicianUser = require_role(UserRole.TECHNICIAN)


@router.post(
    "/upload",
    response_model=CaseUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze a blood image",
)
async def upload_case(
    database: Database,
    settings: Settings = Depends(get_settings),
    current_user: TokenPayload = Depends(TechnicianUser),
    image: UploadFile = File(...),
    patient_id: str = Form(..., min_length=1, max_length=100),
) -> CaseUploadResponse:
    """Persist an upload, reject invalid images, or classify valid smears."""
    image_path, original_filename = await save_image_upload(image, settings)
    try:
        inference = await run_in_threadpool(run_inference, image_path, settings)
    except Exception as exc:
        image_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image processing failed",
        ) from exc

    created_at = datetime.now(timezone.utc)
    case_id = uuid4().hex
    document = {
        "_id": case_id,
        "patient_id": patient_id.strip(),
        "filename": original_filename,
        "stored_path": str(image_path.relative_to(settings.resolve_path(Path(".")))),
        "created_by": current_user.subject,
        "created_at": created_at,
        "status": inference.status.value,
        "priority": int(
            inference.predicted_class is not None
            and inference.predicted_class != "HEALTHY"
        ),
        "doctor_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "inference": inference.model_dump(mode="json"),
    }
    await database["cases"].insert_one(document)
    return CaseUploadResponse(
        case_id=case_id,
        patient_id=document["patient_id"],
        filename=original_filename,
        status=document["status"],
        created_at=created_at,
        inference=inference,
    )


@router.get("/cases", response_model=list[CaseRecord])
async def technician_cases(
    database: Database,
    current_user: TokenPayload = Depends(TechnicianUser),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[CaseRecord]:
    """Return the technician's complete persisted case history."""
    cases = await list_cases(database, created_by=current_user.subject, limit=limit)
    return [
        to_case_record(document, f"/api/v1/technician/case/{document['_id']}/image")
        for document in cases
    ]


@router.get("/case/{case_id}/image")
async def technician_case_image(
    case_id: str,
    database: Database,
    settings: Settings = Depends(get_settings),
    current_user: TokenPayload = Depends(TechnicianUser),
) -> FileResponse:
    """Serve a technician's own uploaded image for history review."""
    document = await get_case(database, case_id)
    if document.get("created_by") != current_user.subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    path = get_case_image_path(document, settings)
    return FileResponse(path, media_type=guess_type(path.name)[0] or "application/octet-stream")
