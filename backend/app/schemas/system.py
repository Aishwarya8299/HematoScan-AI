"""System health and network status response models."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Aggregate health state exposed to the landing page status widget."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    DOWN = "down"


class HealthResponse(BaseModel):
    """Lightweight liveness probe for load balancers and the frontend dashboard."""

    status: ServiceStatus = Field(
        description="Overall API availability indicator."
    )
    service: str = Field(default="hematoscan-api")
    version: str = Field(description="Application semver.")
    environment: str = Field(description="deployment environment label.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of this health check.",
    )
    mongodb_connected: bool = Field(
        default=False,
        description="True when MongoDB ping succeeds (Step 2).",
    )
    ml_models_loaded: bool = Field(
        default=False,
        description="True when both .h5 models are loaded (Step 12).",
    )
