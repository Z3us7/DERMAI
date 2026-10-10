# tests/test_vision_engine.py
"""
Unit tests for the Vision Engine (Rule 02 — TDD).

Uses mock nn.Module objects so no real .pth file is needed.

Covers:
  - Happy path: valid bytes → VisionPrediction returned.
  - InvalidImageError raised on corrupt/non-image bytes.
  - InferenceError raised on model forward pass failure.
  - ModelNotLoadedError raised when engine is constructed with None model.
  - _decode_image_bytes: valid JPEG, valid PNG, corrupt bytes.
  - _map_index_to_prediction: in-bounds index, out-of-bounds index.
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
import torch
from PIL import Image

from app.engine.vision import (
    VisionEngine,
    _decode_image_bytes,
    _map_index_to_prediction,
)
from app.exceptions import InferenceError, InvalidImageError, ModelNotLoadedError
from app.schemas import VisionPrediction

MOCK_CLASSES = ["Class A", "Class B", "Class C"]

# ── Helper: build minimal image bytes ────────────────────────────────────────


def _make_rgb_bytes(fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(255, 0, 0)).save(buf, format=fmt)
    return buf.getvalue()


# ── _decode_image_bytes ───────────────────────────────────────────────────────


class TestDecodeImageBytes:
    def test_valid_jpeg_returns_pil_image(self):
        img = _decode_image_bytes(_make_rgb_bytes("JPEG"))
        assert img.mode == "RGB"

    def test_valid_png_returns_pil_image(self):
        img = _decode_image_bytes(_make_rgb_bytes("PNG"))
        assert img.mode == "RGB"

    def test_empty_bytes_raises_invalid_image_error(self):
        with pytest.raises(InvalidImageError):
            _decode_image_bytes(b"")

    def test_corrupt_bytes_raises_invalid_image_error(self):
        with pytest.raises(InvalidImageError):
            _decode_image_bytes(b"\xff\xd8\xff\x00garbage_data")

    def test_random_bytes_raise_invalid_image_error(self):
        with pytest.raises(InvalidImageError):
            _decode_image_bytes(b"not_an_image_at_all_12345")


# ── _map_index_to_prediction ──────────────────────────────────────────────────


class TestMapIndexToPrediction:
    def test_valid_index_returns_correct_label(self):
        pred = _map_index_to_prediction(class_indices=[0], confidence_scores=[0.95], class_names=MOCK_CLASSES)
        assert pred.predictions[0].disease_name == MOCK_CLASSES[0]
        assert pred.predictions[0].class_index == 0

    def test_last_valid_index_returns_correct_label(self):
        last_index = len(MOCK_CLASSES) - 1
        pred = _map_index_to_prediction(class_indices=[last_index], confidence_scores=[0.7], class_names=MOCK_CLASSES)
        assert pred.predictions[0].disease_name == MOCK_CLASSES[last_index]

    def test_out_of_bounds_index_raises_inference_error(self):
        with pytest.raises(InferenceError):
            _map_index_to_prediction(
                class_indices=[len(MOCK_CLASSES)],
                confidence_scores=[0.5],
                class_names=MOCK_CLASSES,
            )

    def test_negative_index_raises_inference_error(self):
        with pytest.raises(InferenceError):
            _map_index_to_prediction(class_indices=[-1], confidence_scores=[0.5], class_names=MOCK_CLASSES)


# ── VisionEngine.classify_image ───────────────────────────────────────────────


class TestVisionEngineClassifyImage:
    def _make_mock_model(self, num_classes: int = len(MOCK_CLASSES)) -> MagicMock:
        """Build a mock nn.Module that returns a valid logit tensor."""
        model = MagicMock()
        # Return a tensor where index 0 has the highest logit.
        logits = torch.zeros(1, num_classes)
        logits[0, 0] = 10.0
        model.return_value = logits
        return model

    @pytest.mark.asyncio
    async def test_happy_path_returns_vision_prediction(self, valid_jpeg_bytes):
        """Valid image bytes with a mock model returns VisionPrediction."""
        engine = VisionEngine(model=self._make_mock_model(), class_names=MOCK_CLASSES)
        result = await engine.classify_image(image_bytes=valid_jpeg_bytes)
        assert isinstance(result, VisionPrediction)
        assert result.predictions[0].class_index == 0
        assert result.predictions[0].disease_name == MOCK_CLASSES[0]

    @pytest.mark.asyncio
    async def test_corrupt_bytes_raises_invalid_image_error(self):
        """Corrupt bytes should propagate as InvalidImageError."""
        engine = VisionEngine(model=self._make_mock_model(), class_names=MOCK_CLASSES)
        with pytest.raises(InvalidImageError):
            await engine.classify_image(image_bytes=b"garbage")

    @pytest.mark.asyncio
    async def test_none_model_raises_model_not_loaded_error(self, valid_jpeg_bytes):
        """If the model is None, classify_image must raise ModelNotLoadedError."""
        engine = VisionEngine(model=None, class_names=MOCK_CLASSES)
        with pytest.raises(ModelNotLoadedError):
            await engine.classify_image(image_bytes=valid_jpeg_bytes)

    @pytest.mark.asyncio
    async def test_model_runtime_error_raises_inference_error(self, valid_jpeg_bytes):
        """If the model forward pass raises, InferenceError must propagate."""
        model = self._make_mock_model()
        model.side_effect = RuntimeError("CUDA OOM")
        engine = VisionEngine(model=model, class_names=MOCK_CLASSES)
        with pytest.raises(InferenceError):
            await engine.classify_image(image_bytes=valid_jpeg_bytes)
