"""
evals/deps.py
==============
Builds the same client/embeddings/llm objects that main.py builds at
startup (see the `lifespan` function), so every eval script wires
against the REAL project config instead of hardcoding new ones.

Named `deps.py`, not `setup.py` --- `setup` is a loaded/reserved-ish name
in the Python packaging ecosystem (setuptools, build backends) and can
cause import ambiguity in some environments.

    from evals.deps import client, embeddings, llm, COLLECTION_NAME, GOLDENS_DIR
"""
from pathlib import Path

from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient

from rag.config import settings, ROOT_DIR
from rag.rag_service import get_embedding_provider

# goldens/ lives at the project root (same level as src/), NOT inside src/.
# ROOT_DIR already points there (see rag/config.py), so this resolves
# correctly no matter which directory you run `python -m evals.xxx` from.
GOLDENS_DIR = Path(ROOT_DIR) / "goldens"

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