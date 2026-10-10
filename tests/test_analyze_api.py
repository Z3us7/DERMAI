# tests/test_analyze_api.py
"""
Integration tests for POST /api/v1/analyze (Rule 02 — TDD).

Uses the app_client fixture from conftest.py which injects mock engines,
so no real model or GPU is required.

Covers:
  - Happy path: valid JPEG → 200 AnalysisResponse JSON.
  - Happy path: valid PNG → 200 AnalysisResponse JSON.
  - Invalid MIME type → 415.
  - File exceeds size limit → 413.
  - Health check endpoint → 200.
  - Missing file field → 422 (FastAPI validation).
  - Vision engine raises InvalidImageError → 422.
  - Vision engine raises InferenceError → 503.
  - RAG engine raises RagPipelineError → 502.
  - Response JSON matches AnalysisResponse schema fields.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.config import MODEL_VERSION, settings
from app.exceptions import InferenceError, InvalidImageError, RagPipelineError
from app.schemas import AnalysisResponse

# ── Health Check ──────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, app_client: AsyncClient):
        response = await app_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_model_loaded_true(self, app_client: AsyncClient):
        data = (await app_client.get("/health")).json()
        assert data["model_loaded"] is True
        assert data["status"] == "healthy"


# ── Happy Path ────────────────────────────────────────────────────────────────


class TestAnalyzeHappyPath:
    @pytest.mark.asyncio
    async def test_valid_jpeg_returns_200_and_valid_schema(
        self, app_client: AsyncClient, valid_jpeg_bytes: bytes
    ):
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        # Validate that the response matches AnalysisResponse schema
        parsed = AnalysisResponse(**body)
        assert parsed.status == "success"
        assert parsed.model_version == MODEL_VERSION
        assert 0.0 <= parsed.predictions[0].confidence <= 1.0

    @pytest.mark.asyncio
    async def test_valid_png_returns_200(self, app_client: AsyncClient, valid_png_bytes: bytes):
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.png", valid_png_bytes, "image/png")},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_body_contains_all_required_fields(
        self, app_client: AsyncClient, valid_jpeg_bytes: bytes
    ):
        body = (
            await app_client.post(
                "/api/v1/analyze",
                files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
            )
        ).json()
        required_fields = {
            "status",
            "predictions",
            "patient_explanation",
            "rag_context",
            "model_version",
            "processing_time_ms",
        }
        assert required_fields.issubset(body.keys())

    @pytest.mark.asyncio
    async def test_processing_time_is_positive(
        self, app_client: AsyncClient, valid_jpeg_bytes: bytes
    ):
        body = (
            await app_client.post(
                "/api/v1/analyze",
                files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
            )
        ).json()
        assert body["processing_time_ms"] >= 0.0


# ── File Validation Failures ──────────────────────────────────────────────────


class TestAnalyzeFileValidation:
    @pytest.mark.asyncio
    async def test_unsupported_mime_type_returns_415(
        self, app_client: AsyncClient, valid_jpeg_bytes: bytes
    ):
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("doc.pdf", valid_jpeg_bytes, "application/pdf")},
        )
        assert response.status_code == 415
        assert response.json()["detail"]["error_code"] == "UNSUPPORTED_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_unsupported_extension_returns_415(
        self, app_client: AsyncClient, valid_jpeg_bytes: bytes
    ):
        """A JPEG with a .bmp extension should be rejected."""
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.bmp", valid_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 415

    @pytest.mark.asyncio
    async def test_oversized_file_returns_413(self, app_client: AsyncClient):
        """A file exceeding max_upload_size_bytes must return 413."""
        oversized_bytes = b"X" * (settings.max_upload_size_bytes + 1)
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("big.jpg", oversized_bytes, "image/jpeg")},
        )
        assert response.status_code == 413
        assert response.json()["detail"]["error_code"] == "FILE_SIZE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_missing_image_field_returns_422(self, app_client: AsyncClient):
        """FastAPI should return 422 if the 'image' field is absent."""
        response = await app_client.post("/api/v1/analyze")
        assert response.status_code == 422


# ── Engine Failure Propagation ────────────────────────────────────────────────


class TestAnalyzeEngineFailures:
    @pytest.mark.asyncio
    async def test_invalid_image_error_returns_422(
        self,
        app_client: AsyncClient,
        valid_jpeg_bytes: bytes,
        mock_vision_engine: MagicMock,
    ):
        """InvalidImageError from VisionEngine should map to HTTP 422."""
        mock_vision_engine.classify_image = AsyncMock(side_effect=InvalidImageError("Corrupt file"))
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error_code"] == "INVALID_IMAGE"

    @pytest.mark.asyncio
    async def test_inference_error_returns_503(
        self,
        app_client: AsyncClient,
        valid_jpeg_bytes: bytes,
        mock_vision_engine: MagicMock,
    ):
        """InferenceError from VisionEngine should map to HTTP 503."""
        mock_vision_engine.classify_image = AsyncMock(side_effect=InferenceError("Shape mismatch"))
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 503
        assert response.json()["detail"]["error_code"] == "INFERENCE_ERROR"

    @pytest.mark.asyncio
    async def test_rag_pipeline_error_returns_502(
        self,
        app_client: AsyncClient,
        valid_jpeg_bytes: bytes,
        mock_rag_engine: MagicMock,
    ):
        """RagPipelineError should map to HTTP 502."""
        mock_rag_engine.generate_patient_explanation = AsyncMock(
            side_effect=RagPipelineError("LLM timeout")
        )
        response = await app_client.post(
            "/api/v1/analyze",
            files={"image": ("skin.jpg", valid_jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 502
        assert response.json()["detail"]["error_code"] == "RAG_PIPELINE_ERROR"
