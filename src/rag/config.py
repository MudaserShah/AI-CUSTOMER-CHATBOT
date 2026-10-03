#settings for chatbot
#Reads from .env automatically through pydantic-settings
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):

    # openai_api_key: str
    # llm_model: str = "gpt-4o-mini"

    # embedding_provider:str = "openai"
    openrouter_api_key: str
    llm_model: str = "openrouter/free"

    embedding_provider: str = "huggingface"

    qdrant_url: str
    qdrant_api_key:str
    qdrant_collection: str = "customer_knowledge"

    # Database — required, no default. The app must fail to start
    # rather than silently fall back to an insecure/incorrect connection.
    postgres_uri: str

    # Auth — required, no default. Used to sign/verify JWTs.
    # In production this must be a long random secret, kept out of git.
    jwt_secret: str
    jwt_expiry_minutes: int = 60

    # CORS — comma-separated list of allowed origins in production,
    # e.g. "https://app.example.com,https://admin.example.com".
    # Left empty by default so nothing is allowed until explicitly configured.
    cors_allowed_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    #files storage
    # uploads_dir: str= "uploads_tmp"
    uploads_dir: str= "uploads"
    markdown_dir: str= "markdown_files"
    max_upload_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()