"""Application configuration.

Values are loaded from environment variables / a local ``.env`` file. The defaults
are chosen so the API boots and the guest + auth paths work with **zero** external
services (a local SQLite file is used unless ``DATABASE_URL`` is provided).
"""
from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # ``NoDecode`` disables pydantic-settings' default JSON parsing for these
    # list fields so a plain comma-separated env value (e.g.
    # ``CORS_ORIGINS=http://localhost:5173,https://app.example.com``) is accepted
    # and split by the ``mode="before"`` validators below.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    jwt_secret: str = "dev-only-change-this-secret-to-a-32-byte-random-value"
    jwt_ttl_minutes: int = 60 * 24 * 7

    google_client_id: str = ""
    google_client_secret: str = ""
    # Backend callback URL registered in the Google Cloud console. If left blank
    # it is derived from the incoming request at runtime. Must match EXACTLY.
    google_redirect_uri: str = ""
    # Where the browser is sent after a successful OAuth login (the SPA origin).
    frontend_url: str = "http://localhost:5173"

    # --- LLM / RAG -----------------------------------------------------------
    # CareerSetu talks to an OpenAI-compatible LLM gateway (tabitoken.com). Set
    # LLM_API_KEY to the static gateway key; everything else has sane defaults.
    #   LLM_API_KEY=<static bearer key from https://tabitoken.com/keys>
    llm_provider: str = "tabitoken"
    llm_base_url: str = "https://tabitoken.com/"
    llm_api_key: str = "sk-TLd5WVPHZffSqf38NlgMikHVsJZbBrp3mf0vOjkCnh4aHWww"
    # A single model is used for every task (fast + quality alias the same one).
    llm_model: str = "claude-opus-4-8"
    llm_auth_scheme: str = "bearer"  # bearer | raw
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2
    llm_max_tokens: int = 1200
    llm_context_chars: int = 12000

    @property
    def llm_fast_model(self) -> str:
        return self.llm_model

    @property
    def llm_quality_model(self) -> str:
        return self.llm_model

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

    knowledge_admin_emails: Annotated[list[str], NoDecode] = []

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

    @property
    def google_oauth_configured(self) -> bool:
        """True when a full Google OAuth client is configured."""
        return bool(self.google_client_id and self.google_client_secret)

    def is_admin_email(self, email: str | None) -> bool:
        """True when the given email is a CareerSetu knowledge administrator.

        Admins may ingest trusted knowledge PDFs (see the documents module) and
        the SPA uses this flag to reveal the admin-only Knowledge upload page.
        """
        return bool(email) and email.lower() in self.knowledge_admin_emails


settings = Settings()
