# app/engine/rag.py
"""
RAG Engine — LangChain-based medical context pipeline.

Implements RagEngineProtocol. This module provides a modular,
production-ready placeholder that:
  1. Simulates a vector DB retrieval step (returns curated medical snippets).
  2. Formats a structured LangChain prompt for a 6th-grade reading level.
  3. Invokes an LLM (or falls back to a deterministic mock if no API key is set).
  4. Returns the patient explanation + a RagContext audit trail.

Architecture (SRP breakdown):
  _retrieve_medical_context()  → disease name → list[str] (simulated vector DB)
  _build_patient_prompt()      → disease + docs → formatted prompt string
  _invoke_llm()                → prompt → LLM response string
  _build_mock_explanation()    → deterministic fallback (no API key)
  generate_patient_explanation() → public async entry point
"""

from __future__ import annotations

import asyncio
import base64
import logging
import textwrap

from app.config import settings
from app.exceptions import RagPipelineError
from app.schemas import RagContext

logger = logging.getLogger(__name__)


# ── Simulated Vector Database ──────────────────────────────────────────────────
# In production, replace with a real vector store (Chroma, Pinecone, FAISS, etc.)
# Each key maps to a list of medical text snippets for that disease category.

_MEDICAL_KNOWLEDGE_BASE: dict[str, list[str]] = {
    "default": [
        (
            "Skin conditions are very common and most are treatable with the right care. "
            "A dermatologist (skin doctor) can examine your skin and recommend the best treatment."
        ),
        (
            "Early detection of skin conditions leads to better outcomes. "
            "Regular skin checks are recommended, especially if you notice any changes."
        ),
        (
            "Many skin conditions are caused by a combination of genetics and environment. "
            "They are not contagious and are never your fault."
        ),
    ],
    "Melanoma Skin Cancer Nevi and Moles": [
        (
            "Melanoma is a type of skin cancer that starts in cells called melanocytes, "
            "which give skin its color. It is very treatable when caught early."
        ),
        (
            "The ABCDE rule helps spot melanoma: Asymmetry, Border irregularity, "
            "Color variation, Diameter > 6mm, Evolving shape or color."
        ),
        (
            "Most moles are harmless. A doctor should check any mole that changes "
            "in size, shape, or color, or one that bleeds or itches."
        ),
    ],
    "Eczema": [
        (
            "Eczema (atopic dermatitis) makes skin red, itchy, and inflamed. "
            "It is very common in children but can affect anyone."
        ),
        (
            "Triggers include dry skin, soaps, sweat, stress, and certain foods. "
            "Keeping skin moisturised is one of the best ways to manage it."
        ),
        (
            "Eczema is not contagious. Medications like topical corticosteroids "
            "can reduce flare-ups significantly."
        ),
    ],
    "Psoriasis Lichen Planus": [
        (
            "Psoriasis is a chronic skin condition that speeds up the skin cell life cycle, "
            "causing cells to build up rapidly on the surface."
        ),
        (
            "It appears as patches of thick, red skin with silvery scales. "
            "Triggers include stress, infections, and certain medications."
        ),
        (
            "Psoriasis is not contagious. Many effective treatments exist, including "
            "topical creams, light therapy, and oral or injected medications."
        ),
    ],
    "Acne and Rosacea": [
        (
            "Acne is one of the most common skin conditions, affecting millions worldwide. "
            "It occurs when hair follicles become clogged with oil and dead skin cells."
        ),
        (
            "Rosacea causes redness and visible blood vessels in the face. "
            "Triggers include hot drinks, spicy food, sun exposure, and stress."
        ),
        (
            "Both conditions respond well to treatment. A dermatologist can recommend "
            "the right approach for your skin type."
        ),
    ],
}


# ── Private Helpers ───────────────────────────────────────────────────────────


def _retrieve_medical_context(disease_name: str, top_k: int) -> list[str]:
    """
    Simulate a vector database retrieval for a given disease name.

    In production, this would embed the disease_name query and perform
    a cosine similarity search against a real vector store.

    Args:
        disease_name: The disease class predicted by the Vision Engine.
        top_k:        Maximum number of document snippets to return.

    Returns:
        A list of up to top_k medical text snippets.
    """
    documents = _MEDICAL_KNOWLEDGE_BASE.get(disease_name) or _MEDICAL_KNOWLEDGE_BASE["default"]
    return documents[:top_k]


def _build_patient_prompt(disease_name: str, context_documents: list[str]) -> str:
    """
    Format the LangChain prompt for a patient-friendly explanation.

    Args:
        disease_name:       The predicted disease label.
        context_documents:  Retrieved medical snippets for context grounding.

    Returns:
        A fully-formatted prompt string ready to send to an LLM.
    """
    joined_context = "\n".join(f"- {doc}" for doc in context_documents)
    return textwrap.dedent(
        f"""
        You are a compassionate medical AI assistant. A patient has just received a
        preliminary AI skin analysis. Your job is to explain the result in a calm,
        reassuring, and easy-to-understand way.

        RULES:
        - Write at a 6th-grade reading level (age 11-12). Use short, simple sentences.
        - Be reassuring and positive. Do NOT cause panic.
        - Remind the patient that this is an AI screening tool, not a medical diagnosis.
        - Recommend they consult a certified dermatologist for confirmation.
        - Keep your response to 3-4 short paragraphs.

        DIAGNOSIS CONTEXT (from medical knowledge base):
        {joined_context}

        PREDICTED CONDITION: {disease_name}

        Write your patient-friendly explanation below:
    """
    ).strip()


def _build_mock_explanation(disease_name: str, context_documents: list[str]) -> str:
    """
    Generate a deterministic, template-based explanation when no LLM is available.

    This fallback is used when OPENAI_API_KEY is not set, ensuring the
    endpoint is fully functional in development and testing environments.

    Args:
        disease_name:       The predicted disease label.
        context_documents:  Retrieved medical snippets for context grounding.

    Returns:
        A plain-text patient explanation string.
    """
    context_bullet = context_documents[0] if context_documents else "Skin conditions are common."
    return textwrap.dedent(
        f"""
        Our AI has detected signs that may be related to **{disease_name}**.
        Please remember that this is a preliminary screening result, not a medical diagnosis.

        Here is some helpful background: {context_bullet}

        The most important next step is to visit a certified dermatologist (skin doctor)
        who can examine your skin in person and give you the right advice.
        Most skin conditions are very treatable when caught early — so you are doing
        the right thing by getting checked!

        Please do not worry — this tool is here to help you, and a real doctor
        will give you the full picture.
    """
    ).strip()


def _invoke_llm_synchronously(prompt: str) -> str:
    """
    Invoke the LangChain LLM chain synchronously (runs inside a thread pool).

    Uses OpenAI's ChatOpenAI if an API key is configured. Falls back to
    a mock response if no key is available, ensuring dev/test stability.

    Args:
        prompt: The fully-formatted patient explanation prompt.

    Returns:
        The LLM-generated explanation string.

    Raises:
        RagPipelineError: If the LLM call fails with an API or network error.
    """
    if not settings.openai_api_key:
        logger.warning(
            "OPENAI_API_KEY not set. Using deterministic mock RAG response. "
            "Set OPENAI_API_KEY in your .env file to enable real LLM calls."
        )
        # Extract disease name from prompt for mock builder — best-effort parse
        return f"[MOCK LLM RESPONSE]\n\n{prompt}"

    try:
        from langchain_core.messages import HumanMessage
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": settings.llm_model_name,
            "api_key": settings.openai_api_key,
            "temperature": 0.4,
            "max_tokens": 512,
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url

        llm = ChatOpenAI(**kwargs)
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)
    except Exception as exc:
        raise RagPipelineError(detail=str(exc)) from exc


def _invoke_vlm_synchronously(prompt: str, image_bytes: bytes) -> str:
    """
    Invoke a Vision-Language Model (VLM) synchronously (runs inside a thread pool).
    Converts image bytes to base64 and passes them to GPT-4o-mini.
    """
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set. Using mock VLM response.")
        return (
            "[MOCK VLM FALLBACK RESPONSE]\n\n"
            "I am simulating a Vision-Language Fallback because the primary AI was uncertain. "
            "Please add an API key in your .env file to enable actual multi-modal image analysis."
        )

    try:
        from langchain_core.messages import HumanMessage
        from langchain_openai import ChatOpenAI
        
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        kwargs = {
            "model": settings.llm_model_name, # Use configured model name instead of hardcoding gpt-4o-mini
            "api_key": settings.openai_api_key,
            "temperature": 0.4,
            "max_tokens": 512,
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url

        llm = ChatOpenAI(**kwargs)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                },
            ]
        )
        
        response = llm.invoke([message])
        return str(response.content)
    except Exception as exc:
        raise RagPipelineError(detail=str(exc)) from exc


# ── Public Engine Class ───────────────────────────────────────────────────────


class RagEngine:
    """
    LangChain RAG pipeline engine satisfying RagEngineProtocol.

    Orchestrates: retrieve context → build prompt → invoke LLM.
    All synchronous I/O (LLM API call) is dispatched to a thread pool
    to avoid blocking the async event loop.
    """

    async def generate_patient_explanation(
        self,
        disease_name: str,
    ) -> tuple[str, RagContext]:
        """
        Async entry point: generate a patient explanation for a disease diagnosis.

        Args:
            disease_name: The predicted disease label from the Vision Engine.

        Returns:
            A tuple of (patient_explanation, RagContext).

        Raises:
            RagPipelineError: If the LLM invocation fails.
        """
        context_documents = _retrieve_medical_context(
            disease_name=disease_name,
            top_k=settings.rag_top_k_documents,
        )
        prompt = _build_patient_prompt(
            disease_name=disease_name,
            context_documents=context_documents,
        )

        patient_explanation = await asyncio.to_thread(
            _invoke_llm_synchronously,
            prompt,
        )

        rag_context = RagContext(
            retrieved_documents=context_documents,
            prompt_sent_to_llm=prompt,
        )

        logger.info("RAG pipeline complete for disease: %s", disease_name)
        return patient_explanation, rag_context

    async def generate_vision_fallback_explanation(
        self,
        image_bytes: bytes,
    ) -> tuple[str, RagContext]:
        """
        Async entry point: generate an explanation using a multi-modal VLM fallback
        when the primary local classifier is uncertain.
        """
        prompt = (
            "You are a highly skilled medical AI assistant and dermatologist. "
            "Our primary local classifier was uncertain about this skin image. "
            "Please analyze the visual characteristics of this skin lesion, describe what you see, "
            "and provide a differential diagnosis. Keep your response to 3-4 short paragraphs, "
            "write at a 6th-grade reading level, be reassuring, and remind the patient that "
            "this is an AI screening tool, not a medical diagnosis, and they should see a doctor."
        )

        patient_explanation = await asyncio.to_thread(
            _invoke_vlm_synchronously,
            prompt,
            image_bytes,
        )

        rag_context = RagContext(
            retrieved_documents=["(Vision-Language Model Fallback Triggered - No medical database used)"],
            prompt_sent_to_llm=prompt,
        )

        logger.info("VLM fallback pipeline complete.")
        return patient_explanation, rag_context
