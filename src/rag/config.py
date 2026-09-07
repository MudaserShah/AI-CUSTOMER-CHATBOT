#settings for chatbot
#Reads from .env automatically through pydantic-settings
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):

    openai_api_key: str
    llm_model: str = "gpt-4o-mini"

    embedding_provider:str = "openai"

    qdrant_url: str
    qdrant_api_key:str
    qdrant_collection: str = "customer_knowledge"

    #files storage
    uploads_dir: str= "uploads_tmp"
    uploads_dir: str= "uploads"
    markdown_dir: str= "markdown_files"
    max_upload_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()