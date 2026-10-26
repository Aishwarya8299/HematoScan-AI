"""Case upload and persisted inference response models."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.inference import InferenceResult


class CaseUploadResponse(BaseModel):
    """Response returned after an uploaded image is processed."""

    case_id: str
    patient_id: str
    filename: str
    status: str
    created_at: datetime
    inference: InferenceResult


class CaseRecord(BaseModel):
    """Public case summary used by later technician and doctor views."""

    id: str = Field(alias="_id")
    patient_id: str
    filename: str
    status: str
    created_at: datetime
    priority: int = 0
    doctor_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    image_url: str | None = None
    inference: InferenceResult


class CaseReviewUpdate(BaseModel):
    """Doctor's note and optional review completion transition."""

    notes: str = Field(min_length=1, max_length=5000)
    mark_reviewed: bool = False


class CaseQueueItem(BaseModel):
    """Compact case representation for the doctor queue."""

    case_id: str
    patient_id: str
    filename: str
    status: str
    priority: int
    predicted_class: str | None = None
    classifier_confidence: float | None = None
    created_at: datetime
