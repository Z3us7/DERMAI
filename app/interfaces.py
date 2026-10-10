# app/interfaces.py
"""
Behavioral contracts (Protocol interfaces) for the DermAI engine layer.

Defines the abstract behavioral specification for the Vision and RAG engines.
Concrete implementations in app/engine/ must satisfy these contracts.

Per Rule 01 (CONTRACT_FIRST_SPEC): interfaces are defined before
any concrete implementation code.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas import RagContext, VisionPrediction

# ── Vision Engine Interface ───────────────────────────────────────────────────


@runtime_checkable
class VisionEngineProtocol(Protocol):
    """
    Behavioral contract for the computer vision inference engine.

    Implementations must:
      1. Accept raw image bytes.
      2. Decode and pre-process the image (resize → ToTensor → Normalize).
      3. Execute the model forward pass without gradient computation.
      4. Return a VisionPrediction DTO.

    Threading model:
      The public classify_image method is async. Internally, the
      synchronous PyTorch work MUST be dispatched via asyncio.to_thread()
      to avoid blocking the event loop.
    """

    async def classify_image(self, image_bytes: bytes) -> VisionPrediction:
        """
        Perform image classification on raw bytes.

        Args:
            image_bytes: Raw binary content of the uploaded image file.

        Returns:
            VisionPrediction containing the top-1 class name, confidence
            score, and class index.

        Raises:
            InvalidImageError: If the bytes cannot be decoded as a valid image.
            InferenceError:    If the model forward pass raises a runtime error.
            ModelNotLoadedError: If the model has not been loaded into state.
        """
        ...


# ── RAG Engine Interface ──────────────────────────────────────────────────────


@runtime_checkable
class RagEngineProtocol(Protocol):
    """
    Behavioral contract for the LangChain RAG pipeline engine.

    Implementations must:
      1. Accept a disease name string.
      2. Retrieve relevant medical context documents from a vector store.
      3. Format a structured LLM prompt requesting a 6th-grade-level explanation.
      4. Return a patient-friendly explanation string and a RagContext audit trail.
    """

    async def generate_patient_explanation(
        self,
        disease_name: str,
    ) -> tuple[str, RagContext]:
        """
        Generate a patient-friendly explanation for a skin disease diagnosis.

        Args:
            disease_name: The human-readable disease class predicted by the
                          Vision Engine (e.g., "Melanoma Skin Cancer Nevi and Moles").

        Returns:
            A tuple of:
              - patient_explanation (str): Plain-language text at a 6th-grade
                reading level, written to be reassuring and informative.
              - rag_context (RagContext): Audit trail containing the retrieved
                documents and the prompt sent to the LLM.

        Raises:
            RagPipelineError: If document retrieval or LLM generation fails.
        """
        ...
