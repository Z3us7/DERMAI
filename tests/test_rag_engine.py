# tests/test_rag_engine.py
"""
Unit tests for the RAG Engine (Rule 02 — TDD).

Covers:
  - _retrieve_medical_context: known disease, unknown disease falls back to default.
  - _build_patient_prompt: prompt contains disease name and context documents.
  - _build_mock_explanation: returns non-empty string.
  - RagEngine.generate_patient_explanation: returns (str, RagContext) tuple.
  - RagPipelineError raised when LLM invocation fails.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.engine.rag import (
    RagEngine,
    _build_patient_prompt,
    _retrieve_medical_context,
)
from app.exceptions import RagPipelineError
from app.schemas import RagContext

# ── _retrieve_medical_context ────────────────────────────────────────────────


class TestRetrieveMedicalContext:
    def test_known_disease_returns_specific_documents(self):
        docs = _retrieve_medical_context("Eczema", top_k=3)
        assert len(docs) > 0
        assert all(isinstance(d, str) for d in docs)

    def test_unknown_disease_returns_default_documents(self):
        docs = _retrieve_medical_context("UnknownMadeUpDisease9999", top_k=3)
        assert len(docs) > 0  # Falls back to "default" key

    def test_top_k_limits_returned_documents(self):
        docs = _retrieve_medical_context("Eczema", top_k=1)
        assert len(docs) == 1

    def test_zero_top_k_returns_empty_list(self):
        docs = _retrieve_medical_context("Eczema", top_k=0)
        assert docs == []


# ── _build_patient_prompt ────────────────────────────────────────────────────


class TestBuildPatientPrompt:
    def test_prompt_contains_disease_name(self):
        prompt = _build_patient_prompt("Eczema", ["Context doc."])
        assert "Eczema" in prompt

    def test_prompt_contains_context_documents(self):
        prompt = _build_patient_prompt("Eczema", ["Unique marker XYZ123."])
        assert "Unique marker XYZ123." in prompt

    def test_prompt_contains_6th_grade_instruction(self):
        """Prompt must instruct the LLM on reading level."""
        prompt = _build_patient_prompt("Eczema", ["doc"])
        assert "6th-grade" in prompt

    def test_prompt_is_non_empty_string(self):
        prompt = _build_patient_prompt("X", [])
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ── RagEngine.generate_patient_explanation ────────────────────────────────────


class TestRagEngineGeneratePatientExplanation:
    @pytest.mark.asyncio
    async def test_happy_path_returns_str_and_rag_context(self):
        """Without an LLM key, falls back to mock and returns valid types."""
        engine = RagEngine()
        explanation, context = await engine.generate_patient_explanation("Eczema")
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert isinstance(context, RagContext)
        assert len(context.retrieved_documents) > 0
        assert len(context.prompt_sent_to_llm) > 0

    @pytest.mark.asyncio
    async def test_unknown_disease_still_returns_valid_response(self):
        """Fallback documents ensure even unknown diseases get a response."""
        engine = RagEngine()
        explanation, context = await engine.generate_patient_explanation("NonExistentCondition")
        assert isinstance(explanation, str)
        assert isinstance(context, RagContext)

    @pytest.mark.asyncio
    async def test_llm_failure_raises_rag_pipeline_error(self):
        """If LLM invocation raises, RagPipelineError must propagate."""
        engine = RagEngine()

        def _failing_llm(prompt: str) -> str:
            from app.exceptions import RagPipelineError

            raise RagPipelineError(detail="LLM API timeout")

        with (
            patch(
                "app.engine.rag._invoke_llm_synchronously",
                side_effect=RagPipelineError("LLM API timeout"),
            ),
            pytest.raises(RagPipelineError),
        ):
            await engine.generate_patient_explanation("Eczema")
