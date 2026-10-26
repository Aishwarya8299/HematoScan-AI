"""
Application settings loaded from environment variables.

Copy `.env.example` to `.env` at the project root and adjust values per environment.
Model weights are optional until training completes — set ML_MODELS_ENABLED=true when ready.
"""

from functools import lru_cache
from typing import Annotated
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


# Resolve project root (D:\hematoscan\) regardless of cwd when launching uvicorn.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Central configuration for Hematoscan backend services."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="Hematoscan", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # ── Server ───────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # ── Security ─────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=480, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # ── MongoDB (wired in Step 2) ────────────────────────────────────────────
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017", alias="MONGODB_URI"
    )
    mongodb_db_name: str = Field(default="hematoscan", alias="MONGODB_DB_NAME")
    mongodb_server_selection_timeout_ms: int = Field(
        default=1500, alias="MONGODB_SERVER_SELECTION_TIMEOUT_MS"
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default=["http://localhost:5500", "http://127.0.0.1:5500"],
        alias="CORS_ORIGINS",
    )

    # ── Uploads ──────────────────────────────────────────────────────────────
    upload_max_size_mb: int = Field(default=10, alias="UPLOAD_MAX_SIZE_MB")
    upload_dir: Path = Field(default=Path("backend/uploads"), alias="UPLOAD_DIR")

    # ── ML models (optional until .h5 files are available) ───────────────────
    gatekeeper_model_path: Path = Field(
        default=Path("backend/models/gatekeeper_model.h5"),
        alias="GATEKEEPER_MODEL_PATH",
    )
    leukemia_model_path: Path = Field(
        default=Path("backend/models/leukemia_classifier_model.h5"),
        alias="LEUKEMIA_MODEL_PATH",
    )
    ml_models_enabled: bool = Field(default=True, alias="ML_MODELS_ENABLED")
    gatekeeper_valid_threshold: float = Field(
        default=0.5, alias="GATEKEEPER_VALID_THRESHOLD"
    )
    gatekeeper_positive_is_valid: bool = Field(
        default=True, alias="GATEKEEPER_POSITIVE_IS_VALID"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> List[str]:
        """Accept comma-separated string or JSON list from environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return []

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def upload_max_size_bytes(self) -> int:
        return self.upload_max_size_mb * 1024 * 1024

    def resolve_path(self, relative: Path) -> Path:
        """Return an absolute path anchored to the project root."""
        path = relative if relative.is_absolute() else PROJECT_ROOT / relative
        return path.resolve()


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe to inject via FastAPI Depends."""
    return Settings()
