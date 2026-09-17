"""
evals/setup.py
===============
Builds the same client/embeddings/llm objects that main.py builds at
startup (see the `lifespan` function), so every eval script wires
against the REAL project config instead of hardcoding new ones.

    from evals.setup import client, embeddings, llm, COLLECTION_NAME
"""
from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient

from rag.config import settings
from rag.rag_service import get_embedding_provider

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
    timeout=300,
)

embeddings = get_embedding_provider(settings.embedding_provider)

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0,
    api_key=settings.openai_api_key,
)

COLLECTION_NAME = settings.qdrant_collection