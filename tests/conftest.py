# tests/conftest.py
"""
Shared pytest fixtures for the DermAI test suite.

Provides:
  - app_client: An async HTTPX test client with a mocked model state.
  - valid_jpeg_bytes: Minimal valid 1x1 JPEG for happy-path tests.
  - valid_png_bytes: Minimal valid 1x1 PNG for happy-path tests.
  - mock_vision_engine: A mock VisionEngine that returns a fixed prediction.
  - mock_rag_engine: A mock RagEngine that returns a fixed explanation.
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.engine.rag import RagEngine
from app.engine.vision import VisionEngine
from app.main import create_application
from app.schemas import PredictionItem, RagContext, VisionPrediction

# ── Image Byte Fixtures ───────────────────────────────────────────────────────


def _create_in_memory_image(fmt: str) -> bytes:
    """Create a minimal valid image in the given PIL format and return its bytes."""
    buffer = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(100, 149, 237))
    img.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture(scope="session")
def valid_jpeg_bytes() -> bytes:
    """Returns bytes for a minimal valid JPEG image."""
    return _create_in_memory_image("JPEG")


@pytest.fixture(scope="session")
def valid_png_bytes() -> bytes:
    """Returns bytes for a minimal valid PNG image."""
    return _create_in_memory_image("PNG")


# ── Mock Engine Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def fixed_prediction() -> VisionPrediction:
    """A fixed VisionPrediction for deterministic test assertions."""
    return VisionPrediction(
        predictions=[
            PredictionItem(disease_name="Mock Disease A", confidence=0.90, class_index=0),
            PredictionItem(disease_name="Mock Disease B", confidence=0.08, class_index=1),
            PredictionItem(disease_name="Mock Disease C", confidence=0.02, class_index=2),
        ]
    )


@pytest.fixture
def fixed_rag_context() -> RagContext:
    """A fixed RagContext for deterministic test assertions."""
    return RagContext(
        retrieved_documents=["Test medical document snippet."],
        prompt_sent_to_llm="Test prompt.",
    )


@pytest.fixture
def mock_vision_engine(fixed_prediction: VisionPrediction) -> MagicMock:
    """Mock VisionEngine that returns fixed_prediction for any input."""
    engine = MagicMock(spec=VisionEngine)
    engine.classify_image = AsyncMock(return_value=fixed_prediction)
    return engine


@pytest.fixture
def mock_rag_engine(fixed_prediction: VisionPrediction, fixed_rag_context: RagContext) -> MagicMock:
    """Mock RagEngine that returns a fixed (explanation, context) tuple."""
    engine = MagicMock(spec=RagEngine)
    engine.generate_patient_explanation = AsyncMock(
        return_value=("You have a common skin condition. Please see a doctor.", fixed_rag_context)
    )
    return engine


# ── App Client Fixture ────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def app_client(
    mock_vision_engine: MagicMock,
    mock_rag_engine: MagicMock,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTPX test client backed by the FastAPI app.

    Bypasses the lifespan model loading by injecting mock engines directly
    into app.state before requests are made.
    """
    test_app = create_application()

    # Inject mocks directly into app.state to bypass lifespan/model loading.
    test_app.state.vision_engine = mock_vision_engine
    test_app.state.rag_engine = mock_rag_engine

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client
