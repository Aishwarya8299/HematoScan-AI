"""Lazy loading and validation for the local Keras models."""

from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_models(
    gatekeeper_path: str, leukemia_path: str
) -> tuple[Any, Any]:
    """Load both models once per process and validate their input contracts."""
    import tensorflow as tf

    gatekeeper = tf.keras.models.load_model(Path(gatekeeper_path), compile=False)
    leukemia_classifier = tf.keras.models.load_model(
        Path(leukemia_path), compile=False
    )

    expected_input = (None, 128, 128, 3)
    if gatekeeper.input_shape != expected_input:
        raise ValueError(
            f"Gatekeeper input shape {gatekeeper.input_shape} does not match "
            f"expected {expected_input}"
        )
    if leukemia_classifier.input_shape != expected_input:
        raise ValueError(
            "Leukemia classifier input shape "
            f"{leukemia_classifier.input_shape} does not match expected {expected_input}"
        )
    if gatekeeper.output_shape[-1] != 1:
        raise ValueError("Gatekeeper must produce one sigmoid output")
    if leukemia_classifier.output_shape[-1] != 5:
        raise ValueError("Leukemia classifier must produce five class scores")

    return gatekeeper, leukemia_classifier
