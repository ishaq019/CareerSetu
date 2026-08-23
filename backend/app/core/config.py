"""Application configuration.

Values are loaded from environment variables / a local ``.env`` file. The defaults
are chosen so the API boots and the guest + auth paths work with **zero** external
services (a local SQLite file is used unless ``DATABASE_URL`` is provided).
"""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App -----------------------------------------------------------------
    app_name: str = "CareerSetu"
    environment: str = "development"

    # --- Database ------------------------------------------------------------
    # Defaults to a local SQLite file so the app runs out of the box. For
    # production set a Neon/PostgreSQL URL, e.g.
    #   postgresql+psycopg://USER:PASS@HOST-POOLER.REGION.aws.neon.tech/neondb?sslmode=require
    database_url: str = "sqlite:///./careersetu.db"
    database_pool_mode: str = "auto"  # auto | queue | null

    # --- Web / security ------------------------------------------------------
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    jwt_secret: str = "dev-only-change-this-secret-to-a-32-byte-random-value"
    jwt_ttl_minutes: int = 60 * 24 * 7

    google_client_id: str = ""
    google_client_secret: str = ""

    # --- LLM / RAG (Groq is the only supported provider) ---------------------
    llm_provider: str = "groq"
    llm_api_key: str = ""
    llm_fast_model: str = "llama-3.1-8b-instant"
    llm_quality_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_max_tokens: int = 1200
    llm_context_chars: int = 12000

    # --- ChromaDB (vector/knowledge store) -----------------------------------
    # Cloud is preferred: set CHROMA_API_KEY, CHROMA_TENANT and CHROMA_DATABASE
    # to use Chroma Cloud (https://www.trychroma.com/). If no API key is set the
    # store falls back to a self-hosted HTTP server at chroma_host:chroma_port.
    chroma_api_key: str = ""
    chroma_tenant: str = ""
    chroma_database: str = "careersetu"
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # --- Uploads -------------------------------------------------------------
    max_upload_mb: int = 10
    max_text_chars: int = 100_000

    knowledge_admin_emails: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Normalisers ---------------------------------------------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, value):
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        return value

    @field_validator("knowledge_admin_emails", mode="before")
    @classmethod
    def _parse_admins(cls, value):
        if isinstance(value, str):
            return [x.strip().lower() for x in value.split(",") if x.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalise_database_url(cls, value):
        # Neon commonly presents ``postgres://`` URLs. Pin the explicit psycopg
        # dialect so the driver choice is unambiguous, preserving query params.
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://"):]
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://"):]
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_provider)

    @property
    def chroma_cloud(self) -> bool:
        """True when Chroma Cloud credentials are configured."""
        return bool(self.chroma_api_key and self.chroma_tenant)


settings = Settings()
