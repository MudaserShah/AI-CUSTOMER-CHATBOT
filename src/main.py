# main.py — Entry point for Document Butler API.
# Creates the FastAPI app, handles startup/shutdown, includes all routes.
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient

from rag.api_logic import app_state
from rag.config import settings
from rag.rag_service import get_embedding_provider
from rag.routes import router

logging.basicConfig(level=logging.INFO, format="%(levelname)s pip install --upgrade pip| %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all shared resources once at startup."""
    for d in [settings.uploads_dir, settings.uploads_dir, settings.markdown_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger.info("Loading embedding model...")
    app_state["embeddings"] = get_embedding_provider(settings.embedding_provider)

    logger.info("Connecting to Qdrant...")
    app_state["qdrant_client"] = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=300)

    logger.info("Connecting to OpenAI LLM...")
    app_state["llm"] = ChatOpenAI(model=settings.llm_model, temperature=0, api_key=settings.openai_api_key)

    logger.info("Document Butler ready.")
    yield

    app_state.clear()
    logger.info("Server shut down.")


app = FastAPI(
    title       = "AI CUSTOMER CHATBOT",
    description = "Upload files → Ask questions → See exact citations → Open file viewer",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

if __name__ == "__main__":
    import uvicorn