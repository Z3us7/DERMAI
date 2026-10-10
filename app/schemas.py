# app/schemas.py
"""
Pydantic domain models (Data Transfer Objects).

Defines the strict contracts for all data flowing through the API:
  - VisionPrediction  : Output of the Vision Engine
  - RagContext        : Audit trail from the RAG pipeline
  - AnalysisResponse  : The final JSON response returned to callers
  - ErrorResponse     : Structured error body for all HTTPExceptions

Per Rule 01 (CONTRACT_FIRST_SPEC) and Rule 03 (strict typing, no 'any').
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ── Vision Engine Output ──────────────────────────────────────────────────────


class PredictionItem(BaseModel):
    """
    A single disease prediction with its confidence score.
    """
    disease_name: str = Field(
        ...,
        description="Human-readable disease class label.",
        examples=["Melanoma"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax confidence score for this prediction.",
        examples=[0.9342],
    )
    class_index: int = Field(
        ...,
        ge=0,
        description="Raw argmax index from the model's output tensor.",
        examples=[11],
    )

    @field_validator("confidence")
    @classmethod
    def round_confidence_to_four_decimals(cls, value: float) -> float:
        """Normalise precision to avoid floating-point noise in responses."""
        return round(value, 4)


class VisionPrediction(BaseModel):
    """
    The structured output of the non-blocking PyTorch inference pass.

    Attributes:
        predictions: Top-K disease predictions, sorted by confidence (descending).
    """

    predictions: list[PredictionItem] = Field(
        ...,
        description="Top-K predictions from the vision model.",
    )


# ── RAG Engine Output ─────────────────────────────────────────────────────────


class RagContext(BaseModel):
    """
    Audit trail from the LangChain RAG pipeline.

    Included in the response to support debugging and transparency.

    Attributes:
        retrieved_documents: Snippets surfaced from the simulated vector DB.
        prompt_sent_to_llm:  The fully-formatted prompt string.
    """

    retrieved_documents: list[str] = Field(
        ...,
        description="Medical text snippets retrieved from the vector store.",
    )
    prompt_sent_to_llm: str = Field(
        ...,
        description="The exact prompt that was sent to the language model.",
    )


# ── API Success Response ──────────────────────────────────────────────────────


class AnalysisResponse(BaseModel):
    """
    The complete JSON response body for a successful POST /api/v1/analyze call.

    Attributes:
        status:              Always "success" for HTTP 200 responses.
        predictions:         The top-3 class predictions from the vision model.
        patient_explanation: 6th-grade-level text from the LLM based on the #1 prediction.
        rag_context:         Audit trail from the RAG pipeline.
        model_version:       Identifies the model checkpoint in use.
        processing_time_ms:  End-to-end wall-clock time for the request.
    """

    status: Literal["success"] = Field(
        default="success",
        description="Response status discriminator.",
    )
    predictions: list[PredictionItem] = Field(
        ...,
        description="Top-K predicted skin disease classes.",
    )
    patient_explanation: str = Field(
        ...,
        description="LLM-generated, patient-friendly explanation at a 6th-grade reading level.",
    )
    rag_context: RagContext = Field(
        ...,
        description="Audit trail from the RAG pipeline.",
    )
    model_version: str = Field(
        ...,
        description="Identifier for the model checkpoint used.",
        examples=["efficientnet_b3_v1"],
    )
    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Total wall-clock processing time in milliseconds.",
        examples=[312.7],
    )


# ── API Error Response ────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """
    Structured JSON body for all error responses (HTTP 4xx / 5xx).

    Attributes:
        status:     Always "error".
        error_code: Machine-readable slug for programmatic handling.
        detail:     Human-readable description of the failure.
    """

    status: Literal["error"] = Field(default="error")
    error_code: str = Field(
        ...,
        description="Machine-readable error slug.",
        examples=["UNSUPPORTED_FILE_TYPE"],
    )
    detail: str = Field(
        ...,
        description="Human-readable error description.",
    )
