# main.py — Entry point for the AI CUSTOMER CHATBOT API.
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from langchain_openrouter import ChatOpenRouter
from qdrant_client import QdrantClient

from src.agent.agent import close_agent_checkpointer
from src.database.pool import init_pool, close_pool
from src.rag.api_logic import app_state
from src.rag.config import settings
from src.rag.rag_service import get_embedding_provider
from src.rag.routes import router
from src.rate_limit import limiter
from src.routes.auth_routes import router as auth_router
from src.routes.refund_routes import router as refund_router
from src.routes.chat_routes import router as chat_router
from src.routes.order_routes import router as order_router
from src.routes.store_routes import router as store_router
from src.routes.project_routes import router as project_router
from src.routes.widget_routes import router as widget_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all shared resources once at startup."""
    for d in [settings.uploads_dir, settings.markdown_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger.info("Opening PostgreSQL connection pool...")
    init_pool()

    logger.info("Loading embedding model...")
    app_state["embeddings"] = get_embedding_provider(settings.embedding_provider)

    logger.info("Connecting to Qdrant...")
    app_state["qdrant_client"] = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=300,
    )

    logger.info("Connecting to OpenRouter LLM (%s)...", settings.llm_model)
    app_state["llm"] = ChatOpenRouter(
        model=settings.llm_model,
        temperature=0,
    )

    logger.info("AI Customer Chatbot ready.")
    yield

    app_state.clear()
    close_pool()
    close_agent_checkpointer()
    logger.info("Server shut down.")


app = FastAPI(
    title="AI CUSTOMER CHATBOT",
    description="Ecommerce checkout + authenticated customer support AI assistant",
    version="3.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(store_router)
app.include_router(order_router)
app.include_router(refund_router)
app.include_router(chat_router)
app.include_router(project_router)
app.include_router(widget_router)


from fastapi.staticfiles import StaticFiles

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
