# tests/test_schemas.py
"""
Unit tests for Pydantic schema contracts (Rule 02 — TDD).

Covers:
  - VisionPrediction: valid construction, range validation, rounding.
  - RagContext: valid construction, required fields.
  - AnalysisResponse: valid construction, status literal.
  - ErrorResponse: valid construction, field types.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import AnalysisResponse, ErrorResponse, PredictionItem, RagContext, VisionPrediction

# ── VisionPrediction Tests ────────────────────────────────────────────────────


class TestVisionPrediction:
    def test_happy_path_creates_valid_schema(self):
        """Valid inputs produce a correctly populated VisionPrediction."""
        pred = VisionPrediction(
            predictions=[
                PredictionItem(disease_name="Eczema", confidence=0.87654, class_index=5)
            ]
        )
        assert pred.predictions[0].disease_name == "Eczema"
        assert pred.predictions[0].class_index == 5
        assert pred.predictions[0].confidence == pytest.approx(0.8765, abs=1e-3)

    def test_confidence_score_is_rounded_to_four_decimals(self):
        """Validator rounds confidence to 4 decimal places."""
        pred = VisionPrediction(
            predictions=[
                PredictionItem(disease_name="Acne", confidence=0.123456789, class_index=0)
            ]
        )
        assert pred.predictions[0].confidence == 0.1235

    def test_confidence_above_one_raises_validation_error(self):
        """confidence_score > 1.0 must fail validation."""
        with pytest.raises(ValidationError):
            VisionPrediction(predictions=[PredictionItem(disease_name="X", confidence=1.1, class_index=0)])

    def test_confidence_below_zero_raises_validation_error(self):
        """confidence_score < 0.0 must fail validation."""
        with pytest.raises(ValidationError):
            VisionPrediction(predictions=[PredictionItem(disease_name="X", confidence=-0.01, class_index=0)])

    def test_negative_class_index_raises_validation_error(self):
        """class_index < 0 must fail validation."""
        with pytest.raises(ValidationError):
            VisionPrediction(predictions=[PredictionItem(disease_name="X", confidence=0.5, class_index=-1)])

    def test_missing_required_field_raises_validation_error(self):
        """Omitting disease_name must raise ValidationError."""
        with pytest.raises(ValidationError):
            PredictionItem(confidence=0.5, class_index=0)


# ── RagContext Tests ──────────────────────────────────────────────────────────


class TestRagContext:
    def test_happy_path_creates_valid_schema(self):
        """Valid inputs produce a correctly populated RagContext."""
        ctx = RagContext(
            retrieved_documents=["Doc A", "Doc B"],
            prompt_sent_to_llm="Explain eczema simply.",
        )
        assert len(ctx.retrieved_documents) == 2
        assert ctx.prompt_sent_to_llm == "Explain eczema simply."

    def test_empty_document_list_is_valid(self):
        """An empty document list is structurally valid."""
        ctx = RagContext(retrieved_documents=[], prompt_sent_to_llm="prompt")
        assert ctx.retrieved_documents == []

    def test_missing_prompt_raises_validation_error(self):
        """Omitting prompt_sent_to_llm must raise ValidationError."""
        with pytest.raises(ValidationError):
            RagContext(retrieved_documents=[])


# ── AnalysisResponse Tests ────────────────────────────────────────────────────


class TestAnalysisResponse:
    def test_happy_path_creates_valid_schema(self):
        """Valid inputs produce a correctly populated AnalysisResponse."""
        ctx = RagContext(retrieved_documents=["doc"], prompt_sent_to_llm="prompt")
        response = AnalysisResponse(
            predictions=[PredictionItem(disease_name="Eczema", confidence=0.91, class_index=1)],
            patient_explanation="Your skin looks a bit red.",
            rag_context=ctx,
            model_version="v1",
            processing_time_ms=250.5,
        )
        assert response.status == "success"
        assert response.predictions[0].disease_name == "Eczema"

    def test_status_is_always_success_literal(self):
        """status field must always equal 'success'."""
        ctx = RagContext(retrieved_documents=[], prompt_sent_to_llm="p")
        response = AnalysisResponse(
            predictions=[PredictionItem(disease_name="X", confidence=0.5, class_index=1)],
            patient_explanation="OK",
            rag_context=ctx,
            model_version="v1",
            processing_time_ms=10.0,
        )
        assert response.status == "success"

    def test_negative_processing_time_raises_validation_error(self):
        """processing_time_ms < 0 must fail validation."""
        ctx = RagContext(retrieved_documents=[], prompt_sent_to_llm="p")
        with pytest.raises(ValidationError):
            AnalysisResponse(
                predicted_disease="X",
                confidence=0.5,
                patient_explanation="OK",
                rag_context=ctx,
                model_version="v1",
                processing_time_ms=-1.0,
            )


# ── ErrorResponse Tests ───────────────────────────────────────────────────────


class TestErrorResponse:
    def test_happy_path_creates_valid_schema(self):
        """Valid inputs produce a correctly populated ErrorResponse."""
        err = ErrorResponse(error_code="UNSUPPORTED_FILE_TYPE", detail="JPEG only.")
        assert err.status == "error"
        assert err.error_code == "UNSUPPORTED_FILE_TYPE"

    def test_status_is_always_error_literal(self):
        """status field must always equal 'error'."""
        err = ErrorResponse(error_code="CODE", detail="detail")
        assert err.status == "error"
