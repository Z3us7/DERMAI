# app/main.py
"""
DermAI FastAPI Application — Entry Point.

Responsibilities of this module (SRP):
  - Define the lifespan context manager (model loading / teardown).
  - Create and configure the FastAPI application instance.
  - Register middleware (CORS, request logging).
  - Mount routers.
  - Expose health-check and root endpoints.

Model loading is performed EXACTLY ONCE during the lifespan startup phase
and stored in app.state — never at global module scope.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_model_path_at_startup
from app.engine.rag import RagEngine
from app.engine.vision import VisionEngine, load_efficientnet_b3_from_checkpoint
from app.routers import analyze

# ── Logging Configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan Context Manager ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager — runs startup and shutdown logic.

    STARTUP:
      Loads the EfficientNetB3 model from the configured checkpoint path
      exactly once, wraps it in a VisionEngine, and stores both engines
      in app.state for dependency-free access from routers.

    SHUTDOWN:
      Cleans up engine references so garbage collection can reclaim GPU/CPU
      memory held by the model tensors.

    Yields:
        Control to the running application between startup and shutdown.
    """
    logger.info("=== DermAI API Startup — Loading model... ===")
    startup_start = time.perf_counter()

    _load_engines_into_state(app)

    elapsed_ms = (time.perf_counter() - startup_start) * 1000
    logger.info("=== Model loaded in %.1f ms. API ready. ===", elapsed_ms)

    yield  # ← Application runs here

    logger.info("=== DermAI API Shutdown — Releasing model resources. ===")
    _teardown_engines_from_state(app)


def _load_engines_into_state(app: FastAPI) -> None:
    """
    Instantiate and attach the VisionEngine and RagEngine to app.state.

    Args:
        app: The FastAPI application instance.

    Raises:
        FileNotFoundError: If the model checkpoint file does not exist.
        RuntimeError:      If the state dict is incompatible with the architecture.
    """
    validate_model_path_at_startup(settings.resolved_model_path)
    torch_model, class_names = load_efficientnet_b3_from_checkpoint(
        checkpoint_path=str(settings.model_path),
    )
    app.state.vision_engine = VisionEngine(model=torch_model, class_names=class_names)
    app.state.rag_engine = RagEngine()
    logger.info("Engines attached to app.state (num_classes=%d).", len(class_names))


def _teardown_engines_from_state(app: FastAPI) -> None:
    """
    Remove engine references from app.state to allow memory reclamation.

    Args:
        app: The FastAPI application instance.
    """
    app.state.vision_engine = None
    app.state.rag_engine = None
    logger.info("Engine references cleared from app.state.")


# ── Application Factory ───────────────────────────────────────────────────────


def create_application() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.

    Using a factory function (rather than a bare module-level `app`) follows
    the Dependency Inversion Principle: tests can call create_application()
    with overridden settings without touching global state.

    Returns:
        A fully configured FastAPI instance.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "DermAI: Production-grade skin disease classification API. "
            "Powered by EfficientNetB3 and a LangChain RAG pipeline."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    _register_middleware(application)
    _register_routers(application)
    _register_utility_endpoints(application)

    return application


def _register_middleware(app: FastAPI) -> None:
    """
    Attach middleware to the FastAPI application.

    Registers:
      - CORSMiddleware: Configured from settings (never hardcoded origins).
      - Request timing logger: Logs method, path, status, and duration.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_request_timing(request: Request, call_next) -> Response:
        """Log each incoming request's method, path, status code, and duration."""
        request_start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - request_start) * 1000
        logger.info(
            "%s %s → %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def _register_routers(app: FastAPI) -> None:
    """
    Mount all API routers onto the application.

    Args:
        app: The FastAPI application instance.
    """
    app.include_router(analyze.router)


def _register_utility_endpoints(app: FastAPI) -> None:
    """
    Register lightweight utility endpoints (root redirect, health check).

    These endpoints do not depend on the model and are always available.

    Args:
        app: The FastAPI application instance.
    """

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """Redirect root to the interactive API docs."""
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/docs")

    @app.get(
        "/health",
        tags=["Monitoring"],
        summary="Health check",
        description="Returns API health status and model load state.",
    )
    async def health_check(request: Request) -> dict:
        """
        Lightweight liveness probe.

        Returns:
            JSON dict with status, API version, and model readiness flag.
        """
        model_loaded = getattr(request.app.state, "vision_engine", None) is not None
        return {
            "status": "healthy" if model_loaded else "degraded",
            "version": settings.app_version,
            "model_loaded": model_loaded,
        }


# ── Application Instance ───────────────────────────────────────────────────────

app = create_application()
