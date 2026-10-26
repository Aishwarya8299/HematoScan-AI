"""
System endpoints: health checks and network status for the landing page widget.

These routes are intentionally unauthenticated so the public landing page can
display service availability without a login session.
"""

from fastapi import APIRouter, Depends, Request

from app import __version__
from app.core.config import Settings, get_settings
from app.schemas.system import HealthResponse, ServiceStatus

router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API liveness and dependency status",
)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Return current API health.

    ML model status remains disabled until the inference modules are wired in.
    """
    return HealthResponse(
        status=ServiceStatus.OPERATIONAL,
        version=__version__,
        environment=settings.app_env,
        mongodb_connected=getattr(request.app.state, "mongodb_connected", False),
        ml_models_loaded=getattr(request.app.state, "ml_models_loaded", False),
    )
