# app/exceptions.py
"""
Custom exception hierarchy for DermAI.

Defines the failure state contracts per Rule 01 (CONTRACT_FIRST_SPEC).
Every exception carries a human-readable message and a machine-readable
error code string for structured API error responses.
"""

from __future__ import annotations

# ── Root Exception ────────────────────────────────────────────────────────────


class DermAIBaseError(Exception):
    """
    Root exception for all DermAI domain errors.

    All custom exceptions must inherit from this class so callers can
    catch the entire DermAI error family with a single except clause.

    Attributes:
        message: Human-readable description of the failure.
        error_code: Machine-readable slug (e.g. "UNSUPPORTED_FILE_TYPE").
    """

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── Upload Validation Errors ───────────────────────────────────────────────────


class UnsupportedFileTypeError(DermAIBaseError):
    """
    Raised when an uploaded file's MIME type or extension is not
    in the allowed set (JPEG / PNG).

    Maps to HTTP 415 Unsupported Media Type.
    """

    def __init__(self, received_type: str) -> None:
        super().__init__(
            message=f"File type '{received_type}' is not supported. Please upload JPEG or PNG.",
            error_code="UNSUPPORTED_FILE_TYPE",
        )


class FileSizeLimitExceededError(DermAIBaseError):
    """
    Raised when an uploaded file exceeds the configured maximum byte size.

    Maps to HTTP 413 Request Entity Too Large.
    """

    def __init__(self, size_bytes: int, limit_bytes: int) -> None:
        limit_mb = limit_bytes / (1024 * 1024)
        super().__init__(
            message=f"File size {size_bytes} bytes exceeds the {limit_mb:.0f} MB limit.",
            error_code="FILE_SIZE_LIMIT_EXCEEDED",
        )


# ── Image Decoding Errors ──────────────────────────────────────────────────────


class InvalidImageError(DermAIBaseError):
    """
    Raised when raw bytes cannot be decoded into a valid PIL image
    (e.g., file is corrupted or truncated despite a valid MIME type).

    Maps to HTTP 422 Unprocessable Entity.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            message=f"Image could not be decoded: {detail}",
            error_code="INVALID_IMAGE",
        )


# ── Model / Inference Errors ───────────────────────────────────────────────────


class ModelNotLoadedError(DermAIBaseError):
    """
    Raised when a request arrives before the model has been successfully
    loaded into application state during the lifespan startup phase.

    Maps to HTTP 503 Service Unavailable.
    """

    def __init__(self) -> None:
        super().__init__(
            message="The AI model is not loaded. The service may still be initializing.",
            error_code="MODEL_NOT_LOADED",
        )


class InferenceError(DermAIBaseError):
    """
    Raised when the PyTorch forward pass fails for any reason
    (e.g., shape mismatch, NaN output, internal runtime error).

    Maps to HTTP 503 Service Unavailable.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            message=f"Model inference failed: {detail}",
            error_code="INFERENCE_ERROR",
        )


# ── RAG / LLM Errors ─────────────────────────────────────────────────────────


class RagPipelineError(DermAIBaseError):
    """
    Raised when the LangChain RAG pipeline fails during document
    retrieval or LLM generation.

    Maps to HTTP 502 Bad Gateway (upstream dependency failure).
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            message=f"RAG pipeline failed: {detail}",
            error_code="RAG_PIPELINE_ERROR",
        )
