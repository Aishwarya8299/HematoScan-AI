"""Gatekeeper-first orchestration for blood smear classification."""

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import Settings
from app.ml.model_loader import load_models
from app.schemas.inference import (
    ClassPrediction,
    GatekeeperResult,
    InferenceResult,
    InferenceStatus,
)

CLASS_LABELS = ("ALL", "AML", "CLL", "CML", "HEALTHY")
IMAGE_SIZE = (128, 128)


def _prepare_image(image_path: Path) -> np.ndarray:
    """Load an image as a MobileNetV2-compatible float batch."""
    import tensorflow as tf

    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB").resize(IMAGE_SIZE)
        pixels = np.asarray(rgb_image, dtype=np.float32)

    return tf.keras.applications.mobilenet_v2.preprocess_input(
        np.expand_dims(pixels, axis=0)
    )


def _predict(model: Any, batch: np.ndarray) -> np.ndarray:
    """Run inference without training or gradient state."""
    prediction = np.asarray(model.predict(batch, verbose=0))
    if prediction.ndim != 2 or prediction.shape[0] != 1:
        raise ValueError(f"Unexpected model prediction shape: {prediction.shape}")
    return prediction[0]


def run_inference(image_path: Path, settings: Settings) -> InferenceResult:
    """Reject non-smear images before invoking leukemia classification."""
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    gatekeeper, leukemia_classifier = load_models(
        str(settings.resolve_path(settings.gatekeeper_model_path)),
        str(settings.resolve_path(settings.leukemia_model_path)),
    )
    batch = _prepare_image(image_path)
    gatekeeper_score = float(_predict(gatekeeper, batch)[0])
    threshold = settings.gatekeeper_valid_threshold
    is_blood_smear = (
        gatekeeper_score >= threshold
        if settings.gatekeeper_positive_is_valid
        else gatekeeper_score < threshold
    )
    gatekeeper_confidence = (
        gatekeeper_score if is_blood_smear else 1.0 - gatekeeper_score
    )
    gatekeeper_result = GatekeeperResult(
        is_blood_smear=is_blood_smear,
        confidence=gatekeeper_confidence,
    )

    if not is_blood_smear:
        return InferenceResult(
            status=InferenceStatus.REJECTED,
            gatekeeper=gatekeeper_result,
            rejection_reason="Image was rejected by the blood-smear gatekeeper",
        )

    probabilities = _predict(leukemia_classifier, batch)
    if probabilities.shape[0] != len(CLASS_LABELS):
        raise ValueError(
            f"Expected {len(CLASS_LABELS)} classifier scores, got {probabilities.shape[0]}"
        )
    best_index = int(np.argmax(probabilities))
    return InferenceResult(
        status=InferenceStatus.AWAITING_REVIEW,
        gatekeeper=gatekeeper_result,
        predicted_class=CLASS_LABELS[best_index],
        classifier_confidence=float(probabilities[best_index]),
        class_probabilities=[
            ClassPrediction(label=label, probability=float(probability))
            for label, probability in zip(CLASS_LABELS, probabilities)
        ],
    )
