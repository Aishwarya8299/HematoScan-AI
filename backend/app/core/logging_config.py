"""
Structured logging configuration for clinical audit trails.

Log format is JSON-friendly in production and human-readable in development.
"""

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(*, debug: bool = False, app_name: str = "Hematoscan") -> None:
    """
    Configure root logger once at application startup.

    Args:
        debug: When True, emit DEBUG-level messages.
        app_name: Included in log record format for multi-service deployments.
    """
    level = logging.DEBUG if debug else logging.INFO

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        f"{app_name} | %(message)s"
    )

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Quiet noisy third-party loggers in development.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the hematoscan hierarchy."""
    return logging.getLogger(f"hematoscan.{name}")
