"""
Central configuration — reads from .env via pydantic-settings.
All services import from here; no raw os.getenv() elsewhere.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]   # repo root
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
ASSISTANTS_DIR = Path(__file__).resolve().parents[1] / "assistants"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ───────────────────────────────────────────────────────────
    openai_api_key: str
    # Accept both OPENAI_MODEL and OPENAI_CHAT_MODEL (env uses OPENAI_MODEL)
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    @property
    def openai_chat_model(self) -> str:
        return self.openai_model

    # ── Pinecone ──────────────────────────────────────────────────────
    pinecone_api_key: str
    pinecone_index_name: str = "jamiiz-ai-demo"
    pinecone_ns_website: str = "jamiiz-website"
    pinecone_ns_property: str = "property-demo"
    pinecone_ns_document: str = "document-demo"
    pinecone_ns_nonprofit: str = "nonprofit-demo"

    # ── App ───────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── LangSmith ─────────────────────────────────────────────────────
    # Accept both LANGSMITH_API_KEY and LANGCHAIN_API_KEY (env uses LANGSMITH_API_KEY)
    langchain_tracing_v2: bool = False
    langsmith_api_key: str = ""
    langsmith_tracing: bool = False
    langchain_project: str = "jamiiz-ai-demos"

    @property
    def langchain_api_key(self) -> str:
        return self.langsmith_api_key

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    def namespace_for(self, assistant_type: str) -> str:
        mapping = {
            "website":   self.pinecone_ns_website,
            "property":  self.pinecone_ns_property,
            "document":  self.pinecone_ns_document,
            "nonprofit": self.pinecone_ns_nonprofit,
        }
        ns = mapping.get(assistant_type)
        if not ns:
            raise ValueError(f"Unknown assistant_type: {assistant_type!r}")
        return ns


@lru_cache
def get_settings() -> Settings:
    return Settings()
