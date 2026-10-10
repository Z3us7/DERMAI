# app/config.py
"""
Application configuration module.

Loads all settings from environment variables / .env file using
pydantic-settings. Zero secrets or magic values in business logic
(Rule 03 — Zero Magic Values; Rule 05 Phase 3 — no secrets in code).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Image Processing Constants ────────────────────────────────────────────────
IMAGE_INPUT_SIZE: int = 300
IMAGENET_MEAN: tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: tuple[float, float, float] = (0.229, 0.224, 0.225)

# ── Allowed Upload Types ───────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png"})
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})

# ── Disease Class Labels ───────────────────────────────────────────────────────
# Labels are no longer hardcoded here. They are dynamically extracted from the
# model checkpoint's `idx_to_class` dictionary during server startup.

# ── Model API Version ─────────────────────────────────────────────────────────
MODEL_VERSION: str = "efficientnet_b3_v1"


class AppSettings(BaseSettings):
    """
    Central application settings.

    All values are read from environment variables or a .env file.
    Sensitive fields (e.g., API keys) must never have hardcoded defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    app_name: str = Field(default="DermAI API", description="Human-readable API name.")
    app_version: str = Field(default="1.0.0", description="Semantic API version.")
    debug: bool = Field(default=False, description="Enable debug mode (never True in prod).")

    # ── Model ─────────────────────────────────────────────────────────────────
    model_path: Path = Field(
        default=Path("DermAI_Mega_Payload.pth"),
        description="Path to the .pth model checkpoint, relative to CWD.",
    )

    # ── Upload Limits ─────────────────────────────────────────────────────────
    max_upload_size_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum allowed upload file size in bytes.",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allow_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins. Restrict in production.",
    )

    # ── LangChain / LLM ───────────────────────────────────────────────────────
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for LLM calls. Leave unset to use mock RAG.",
    )
    llm_model_name: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier used by the RAG engine.",
    )
    llm_base_url: str | None = Field(
        default=None,
        description="Optional Base URL to override the default OpenAI endpoint (e.g., for Groq, OpenRouter, TogetherAI).",
    )
    rag_top_k_documents: int = Field(
        default=3,
        description="Number of documents retrieved from the simulated vector DB.",
    )

    @property
    def resolved_model_path(self) -> Path:
        """Return the resolved absolute path to the model checkpoint."""
        return self.model_path.resolve()


def validate_model_path_at_startup(path: Path) -> None:
    """
    Validate that the model checkpoint file exists.

    Called explicitly during the lifespan startup phase rather than at
    import time, so tests can import app modules without needing the .pth file.

    Args:
        path: Resolved path to the model checkpoint file.

    Raises:
        FileNotFoundError: If the checkpoint does not exist at the given path.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found at '{path}'. "
            "Ensure DermAI_Mega_Payload.pth is present in the working directory."
        )


# Singleton settings instance imported across the application.
settings = AppSettings()
