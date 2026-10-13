from langchain_core.tools import tool
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.rag.config import settings
from src.rag.rag_service import get_embedding_provider


embeddings = get_embedding_provider(
    settings.embedding_provider
)

qdrant_client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)


def search_knowledge_base_for_project(question: str, project_id: str = "technest-default") -> str:
    """
    Search knowledge base scoped strictly to a specific project.
    Prevents cross-tenant knowledge leaks.
    """
    query_vector = embeddings.embed_query(question)

    query_filter = Filter(
        must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))]
    )

    results = qdrant_client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=query_filter,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )

    if not results.points:
        return "I couldn't find relevant information in the knowledge base."

    context_parts = []
    for hit in results.points:
        payload = hit.payload
        context_parts.append(payload["chunk_text"])

    return "\n\n---\n\n".join(context_parts)


@tool
def search_knowledge_base(question: str) -> str:
    """
    Search the customer support knowledge base and return
    relevant information for answering the customer's question.
    """
    return search_knowledge_base_for_project(question, project_id="technest-default")