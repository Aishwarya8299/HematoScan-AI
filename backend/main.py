"""
Hematoscan — FastAPI application entry point.

Run locally:
    cd D:\hematoscan\backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

OpenAPI docs: http://localhost:8000/docs
Health check:  http://localhost:8000/api/v1/system/health
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging_config import get_logger, setup_logging
from app.db.mongodb import close_mongodb, connect_mongodb, ensure_indexes, get_database
from app.ml.model_loader import load_models

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application startup and shutdown hooks.

    MongoDB and ML model connections are initialized before serving requests.
    """
    settings = get_settings()
    setup_logging(debug=settings.debug, app_name=settings.app_name)

    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        __version__,
        settings.app_env,
    )

    mongodb_client = await connect_mongodb(settings)
    app.state.mongodb_client = mongodb_client
    app.state.mongodb_connected = mongodb_client is not None
    app.state.database = get_database(mongodb_client, settings)
    await ensure_indexes(app.state.database)

    if settings.is_production and settings.jwt_secret_key == "change-me":
        logger.warning(
            "JWT_SECRET_KEY is still the default — rotate before production deploy."
        )

    # Ensure upload directories exist (used from Step 8 onward).
    for subdir in ("raw", "processed", "reports"):
        upload_path = settings.resolve_path(settings.upload_dir) / subdir
        upload_path.mkdir(parents=True, exist_ok=True)
        logger.debug("Upload directory ready: %s", upload_path)

    app.state.ml_models_loaded = False
    if settings.ml_models_enabled:
        load_models(
            str(settings.resolve_path(settings.gatekeeper_model_path)),
            str(settings.resolve_path(settings.leukemia_model_path)),
        )
        app.state.ml_models_loaded = True
        logger.info("Gatekeeper and leukemia classifier models loaded.")
    else:
        logger.info(
            "ML models disabled (ML_MODELS_ENABLED=false)."
        )

    yield

    await close_mongodb(mongodb_client)
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory — used by uvicorn and test clients."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "B2B Diagnostic Decision Support System for hospital "
            "Lab Technicians and Doctors."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Minimal root redirect target for sanity checks."""
        return {
            "service": settings.app_name,
            "version": __version__,
            "health": f"{settings.api_v1_prefix}/system/health",
            "docs": "/docs",
        }

    return app


app = create_app()
