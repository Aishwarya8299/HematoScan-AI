"""Inference request and result models."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class InferenceStatus(str, Enum):
    """Pipeline state after gatekeeper and classifier decisions."""

    REJECTED = "rejected"
    AWAITING_REVIEW = "awaiting_review"


class GatekeeperResult(BaseModel):
    """The gatekeeper decision and confidence score."""

    is_blood_smear: bool
    confidence: float = Field(ge=0, le=1)


class ClassPrediction(BaseModel):
    """One leukemia class probability."""

    label: str
    probability: float = Field(ge=0, le=1)


class InferenceResult(BaseModel):
    """Full gated inference result."""

    status: InferenceStatus
    gatekeeper: GatekeeperResult
    predicted_class: str | None = None
    classifier_confidence: float | None = Field(default=None, ge=0, le=1)
    class_probabilities: list[ClassPrediction] = Field(default_factory=list)
    rejection_reason: str | None = None
