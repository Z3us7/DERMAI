# app/routers/analyze.py
"""
POST /api/v1/analyze — Skin disease analysis endpoint.

Handles the full request lifecycle:
  1. File type validation (MIME + extension whitelist).
  2. File size guard.
  3. Non-blocking Vision Engine inference (asyncio.to_thread).
  4. RAG Engine patient explanation generation.
  5. Structured Pydantic response assembly.
  6. Exception → HTTPException translation with structured error bodies.

Architecture (SRP):
  _validate_file_type()   → guards MIME and extension
  _validate_file_size()   → guards byte length
  _read_upload_bytes()    → reads UploadFile safely with cleanup
  analyze_image()         → endpoint orchestrator (≤ 30 lines of logic)
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from app.config import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MODEL_VERSION,
    settings,
)
from app.exceptions import (
    DermAIBaseError,
    FileSizeLimitExceededError,
    InferenceError,
    InvalidImageError,
    ModelNotLoadedError,
    RagPipelineError,
    UnsupportedFileTypeError,
)
from app.schemas import AnalysisResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])


# ── Exception → HTTP Status Code Mapping ─────────────────────────────────────

_EXCEPTION_STATUS_MAP: dict[type[DermAIBaseError], int] = {
    UnsupportedFileTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    FileSizeLimitExceededError: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    InvalidImageError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ModelNotLoadedError: status.HTTP_503_SERVICE_UNAVAILABLE,
    InferenceError: status.HTTP_503_SERVICE_UNAVAILABLE,
    RagPipelineError: status.HTTP_502_BAD_GATEWAY,
}


# ── Private Validation Helpers ────────────────────────────────────────────────


def _validate_file_type(file: UploadFile) -> None:
    """
    Guard: validate MIME content-type and filename extension.

    Uses a two-layer check (MIME header + extension) for defense in depth.

    Args:
        file: The FastAPI UploadFile from the multipart form request.

    Raises:
        UnsupportedFileTypeError: If MIME type or extension is not allowed.
    """
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(received_type=content_type)

    filename = file.filename or ""
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(received_type=suffix)


def _validate_file_size(raw_bytes: bytes) -> None:
    """
    Guard: validate that the uploaded file does not exceed the size limit.

    Args:
        raw_bytes: The fully-read file content.

    Raises:
        FileSizeLimitExceededError: If byte length exceeds the configured limit.
    """
    if len(raw_bytes) > settings.max_upload_size_bytes:
        raise FileSizeLimitExceededError(
            size_bytes=len(raw_bytes),
            limit_bytes=settings.max_upload_size_bytes,
        )


async def _read_upload_file_safely(file: UploadFile) -> bytes:
    """
    Read all bytes from an UploadFile and guarantee the file handle is closed.

    Args:
        file: The FastAPI UploadFile to read.

    Returns:
        Raw bytes of the uploaded file.

    Raises:
        HTTPException (500): If an unexpected I/O error occurs during reading.
    """
    try:
        return await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read the uploaded file. Please try again.",
        ) from exc
    finally:
        await file.close()


def _domain_error_to_http_exception(exc: DermAIBaseError) -> HTTPException:
    """
    Translate a DermAIBaseError subclass into a FastAPI HTTPException.

    Args:
        exc: The domain exception raised by an engine or validator.

    Returns:
        An HTTPException with the correct status code and structured body.
    """
    http_status = _EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    error_body = ErrorResponse(error_code=exc.error_code, detail=exc.message)
    return HTTPException(status_code=http_status, detail=error_body.model_dump())


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a skin image for disease classification",
    description=(
        "Accepts a JPEG or PNG skin image upload. Runs it through the "
        "EfficientNetB3 vision model and a LangChain RAG pipeline to return "
        "a predicted skin disease class and a patient-friendly explanation."
    ),
    responses={
        200: {"model": AnalysisResponse},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
        422: {"model": ErrorResponse, "description": "Invalid or corrupt image"},
        503: {"model": ErrorResponse, "description": "Model not ready or inference failed"},
    },
)
async def analyze_image(
    request: Request,
    image: UploadFile,
) -> AnalysisResponse:
    """
    POST /api/v1/analyze — Skin disease analysis endpoint.

    Orchestration flow:
      validate type → read bytes → validate size → vision inference
      → RAG explanation → assemble response

    Args:
        request: FastAPI request object (used to access application state).
        image:   Multipart file upload (JPEG or PNG skin image).

    Returns:
        AnalysisResponse with prediction, explanation, and metadata.

    Raises:
        HTTPException: For all validation, inference, or pipeline failures.
    """
    request_start_time = time.perf_counter()

    try:
        _validate_file_type(file=image)
        raw_bytes = await _read_upload_file_safely(file=image)
        _validate_file_size(raw_bytes=raw_bytes)

        vision_engine = request.app.state.vision_engine
        rag_engine = request.app.state.rag_engine

        prediction = await vision_engine.classify_image(image_bytes=raw_bytes)
        
        top_prediction = prediction.predictions[0]
        patient_explanation, rag_context = await rag_engine.generate_patient_explanation(
            disease_name=top_prediction.disease_name
        )

        processing_time_ms = (time.perf_counter() - request_start_time) * 1000

        logger.info(
            "Request complete: top_disease=%s, top_confidence=%.4f, time_ms=%.1f",
            top_prediction.disease_name,
            top_prediction.confidence,
            processing_time_ms,
        )

        return AnalysisResponse(
            predictions=prediction.predictions,
            patient_explanation=patient_explanation,
            rag_context=rag_context,
            model_version=MODEL_VERSION,
            processing_time_ms=round(processing_time_ms, 2),
        )

    except DermAIBaseError as exc:
        logger.warning("Domain error in analyze endpoint: [%s] %s", exc.error_code, exc.message)
        raise _domain_error_to_http_exception(exc) from exc

    except HTTPException:
        raise  # Re-raise FastAPI HTTPExceptions (e.g., from _read_upload_file_safely)

    except Exception as exc:
        logger.critical("Unexpected error in analyze endpoint: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                detail="An unexpected internal error occurred. Please contact support.",
            ).model_dump(),
        ) from exc
