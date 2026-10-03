# main.py — Entry point for Document Butler API.
# Creates the FastAPI app, handles startup/shutdown, includes all routes.
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
# from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from qdrant_client import QdrantClient

from src.database.pool import init_pool, close_pool
from src.rag.api_logic import app_state
from src.rag.config import settings
from src.rag.rag_service import get_embedding_provider
from src.rag.routes import router
from src.rate_limit import limiter
from src.routes.auth_routes import router as auth_router
from src.routes.refund_routes import router as refund_router
from src.routes.chat_routes import router as chat_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all shared resources once at startup."""
    for d in [settings.uploads_dir, settings.uploads_dir, settings.markdown_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger.info("Opening PostgreSQL connection pool...")
    init_pool()

    logger.info("Loading embedding model...")
    app_state["embeddings"] = get_embedding_provider(settings.embedding_provider)

    logger.info("Connecting to Qdrant...")
    app_state["qdrant_client"] = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=300)

    # logger.info("Connecting to OpenAI LLM...")
    # app_state["llm"] = ChatOpenAI(model=settings.llm_model, temperature=0, api_key=settings.openai_api_key)
    
    logger.info("Connecting to OpenRouter LLM...")
    app_state["llm"] = ChatOpenRouter(
    model="openrouter/free",
    temperature=0,
    )

    logger.info("Document Butler ready.")
    yield

    app_state.clear()
    close_pool()
    logger.info("Server shut down.")


app = FastAPI(
    title       = "AI CUSTOMER CHATBOT",
    description = "Upload files → Ask questions → See exact citations → Open file viewer",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS: no wildcard. cors_origins_list is empty by default (see
# src/rag/config.py) — set CORS_ALLOWED_ORIGINS in .env to your real
# frontend domain(s) before this is reachable from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(refund_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )