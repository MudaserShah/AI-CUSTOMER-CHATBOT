import asyncio
import hashlib
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)
from rag.file_loaders import load_file
from rag.markdown_generator import generate_markdown, smart_chunk
from rag.schemas import Citation
from rag.config import Settings

logger = logging.getLogger(__name__)


def compute_doc_id(file_name: str) -> str:
    """
    create a determinitic ID from the file name
    same file -> same doc_id
    """
    return hashlib.sha256(file_name.encode("utf-8")).hexdigest()[:16]


def get_embedding_provider(provider: str):
    """
    Return the configured embedding model.

    OpenAI:
        text-embedding-3-small → 1536 dimensions

    HuggingFace:
        all-MiniLM-L6-v2 → 384 dimension
    """
    settings = Settings()
    api_key = getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "openai_api_key", None)
    if provider == "openai":
        return OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
    return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
            )
    
    # return HuggingFaceEmbeddings(
    #     model_name="all-MiniLM-L6-v2"
    # )

def collection_exists(
        client: QdrantClient,
        collection_name: str
) -> bool:
    """
    Check whether a Qdrant collection exists.
    """
    collections = client.get_collections().collections
    return collection_name in [collection.name for collection in collections]


def ensure_collection(
        client: QdrantClient,
        collection_name: str,
        vector_size: int,
):
    """
    Create Qdrant collection if it does not exist.

    Also creates an index on doc_id so documents
    can later be deleted efficiently.
    """
    if not collection_exists(client, collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            ),
        )
        logger.info(
            "Created collection '%s' with vector size %s",
            collection_name,
            vector_size,
        )

    client.create_payload_index(
        collection_name=collection_name,
        field_name="doc_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )

def index_document(
    file_path: str,
    file_name: str,
    client: QdrantClient,
    embeddings,
    collection_name: str,
    uploads_dir: str,
    markdown_dir: str,
) -> dict:
    """
    Complete document indexing pipeline.

    Steps:

    1. Load file
    2. Save original file
    3. Generate markdown
    4. Save markdown
    5. Smart chunk markdown
    6. Create embeddings
    7. Store chunks + metadata in Qdrant
    """

    logger.info(
        "Starting indexing for '%s'",
        file_name,
    )

    doc_id = compute_doc_id(file_name)

    extension = Path(file_name).suffix.lower()

    upload_timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    docs: List[Document] = load_file(
        file_path=file_path,
        file_name=file_name,
    )

    logger.info(
        "Loaded %s document(s)",
        len(docs),
    )

    for doc in docs:
        doc.page_content = (
            doc.page_content
            .encode(
                "utf-8",
                errors="replace",
            )
            .decode("utf-8")
        )

    os.makedirs(
        uploads_dir,
        exist_ok=True,
    )

    original_path = os.path.join(
        uploads_dir,
        f"{doc_id}{extension}",
    )

    shutil.copy2(
        file_path,
        original_path,
    )

    logger.info(
        "Original file saved → %s",
        original_path,
    )

    markdown_text = generate_markdown(
        docs=docs,
        file_name=file_name,
    )

    os.makedirs(
        markdown_dir,
        exist_ok=True,
    )

    markdown_path = os.path.join(
        markdown_dir,
        f"{doc_id}.md",
    )

    with open(
        markdown_path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(markdown_text)

    logger.info(
        "Markdown saved → %s",
        markdown_path,
    )

    chunks = smart_chunk(
        markdown_text
    )

    table_count = sum(
        1
        for chunk in chunks
        if chunk.get("is_table", False)
    )

    logger.info(
        "Created %s chunks (%s tables)",
        len(chunks),
        table_count,
    )

    if not chunks:
        logger.warning(
            "No chunks produced for '%s'",
            file_name,
        )

        return {
            "doc_id": doc_id,
            "file_name": file_name,
            "file_type": extension.lstrip("."),
            "total_chunks": 0,
            "total_pages": len(docs),
            "upload_timestamp": upload_timestamp,
        }

    page_numbers = [
        chunk.get("page_number")
        for chunk in chunks
        if chunk.get("page_number") is not None
    ]

    total_pages = max(
        page_numbers,
        default=1,
    )

    points: List[PointStruct] = []

    collection_ready = False

    for chunk_index, chunk in enumerate(chunks):

        text = chunk["text"]

        # Convert chunk text into vector.
        vector = embeddings.embed_query(
            text
        )

        # Create Qdrant collection using
        # the dimension of the first vector.
        if not collection_ready:

            ensure_collection(
                client=client,
                collection_name=collection_name,
                vector_size=len(vector),
            )

            collection_ready = True

        payload = {
            "file_name": file_name,

            "file_type": extension.lstrip("."),

            "page_number": chunk.get(
                "page_number",
                1,
            ),

            "chunk_index": chunk_index,

            "doc_id": doc_id,

            "chunk_text": text,

            "is_table": chunk.get(
                "is_table",
                False,
            ),

            "markdown_path": markdown_path,

            "original_path": original_path,

            "total_pages": total_pages,

            "upload_timestamp": upload_timestamp,
        }

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points,
    )

    logger.info(
        "Indexed %s chunks into '%s'",
        len(points),
        collection_name,
    )

    return {
        "doc_id": doc_id,
        "file_name": file_name,
        "file_type": extension.lstrip("."),
        "total_chunks": len(points),
        "total_pages": total_pages,
        "upload_timestamp": upload_timestamp,
    }


def query_with_citations(
    question: str,
    top_k: int,
    client: QdrantClient,
    embeddings,
    llm: ChatOpenAI,
    collection_name: str,
) -> dict:
    """
    Search Qdrant and generate an answer with citations.

    Flow:

        Question
            ↓
        Embedding
            ↓
        Qdrant Search
            ↓
        Relevant Chunks
            ↓
        Context
            ↓
        LLM
            ↓
        Answer + References
    """

    if not collection_exists(
        client,
        collection_name,
    ):
        return {
            "answer": (
                "No documents have been uploaded yet. "
                "Please upload a file first."
            ),
            "references": [],
        }


    query_vector = embeddings.embed_query(
        question
    )

    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    if not results.points:
        return {
            "answer": (
                "I couldn't find any relevant information "
                "in the uploaded documents."
            ),
            "references": [],
        }

    citations: List[Citation] = []

    context_parts: List[str] = []

    for hit in results.points:

        payload = hit.payload

        citations.append(
            Citation(
                file_name=payload["file_name"],

                page_number=payload.get(
                    "page_number",
                    1,
                ),

                chunk_index=payload[
                    "chunk_index"
                ],

                chunk_text=payload[
                    "chunk_text"
                ],

                relevance_score=round(
                    hit.score,
                    4,
                ),

                doc_id=payload[
                    "doc_id"
                ],

                is_table=payload.get(
                    "is_table",
                    False,
                ),
            )
        )

        context_parts.append(
            (
                f"[Source: "
                f"{payload['file_name']}, "
                f"page "
                f"{payload.get('page_number', 1)}]"
                f"\n"
                f"{payload['chunk_text']}"
            )
        )

    # Combine all chunks.
    context = "\n\n---\n\n".join(
        context_parts
    )


    prompt = ChatPromptTemplate.from_template(
        """
You are a precise document analyst.

Answer the user's question using ONLY the context below.

Do not use outside knowledge.

Do not mention file names or page numbers in your answer.
Those will be shown separately as citations.

If the answer cannot be found in the context, say:

"I couldn't find that in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""
    )


    chain = (
        prompt
        | llm
        | StrOutputParser()
    )


    answer = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )
                

    return {
        "answer": answer,
        "references": citations,
    }

async def query_stream(
    question: str,
    top_k: int,
    client: QdrantClient,
    embeddings,
    llm: ChatOpenAI,
    collection_name: str,
) -> AsyncGenerator[str, None]:
    """
    Streaming version of query_with_citations().

    Events:

        citations
            ↓
        token
            ↓
        token
            ↓
        token
            ↓
        done
    """


    def _sse(payload: dict) -> str:
        return (
            f"data: "
            f"{json.dumps(payload)}"
            f"\n\n"
        )

    

    if not collection_exists(
        client,
        collection_name,
    ):
        yield _sse(
            {
                "type": "error",
                "message": (
                    "No documents uploaded yet. "
                    "Please upload a file first."
                ),
            }
        )
        return

   
    query_vector = await asyncio.to_thread(
        embeddings.embed_query,
        question,
    )


    results = await asyncio.to_thread(
        lambda: client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
    )

    if not results.points:
        yield _sse(
            {
                "type": "error",
                "message": (
                    "I couldn't find any relevant "
                    "information in the uploaded documents."
                ),
            }
        )
        return


    citations: list = []

    context_parts: list = []

    for hit in results.points:

        payload = hit.payload

 
        citations.append(
            {
                "file_name": payload[
                    "file_name"
                ],

                "page_number": payload.get(
                    "page_number",
                    1,
                ),

                "chunk_index": payload[
                    "chunk_index"
                ],

                "chunk_text": payload[
                    "chunk_text"
                ],

                "relevance_score": round(
                    hit.score,
                    4,
                ),

                "doc_id": payload[
                    "doc_id"
                ],

                "is_table": payload.get(
                    "is_table",
                    False,
                ),
            }
        )


        context_parts.append(
            (
                f"[Source: "
                f"{payload['file_name']}, "
                f"page "
                f"{payload.get('page_number', 1)}]"
                f"\n"
                f"{payload['chunk_text']}"
            )
        )

    yield _sse(
        {
            "type": "citations",
            "data": citations,
        }
    )

    context = "\n\n---\n\n".join(
        context_parts
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a precise document analyst.

Answer the user's question using ONLY the context below.

Do not use outside knowledge.

Do not mention file names or page numbers in your answer.
Those will be shown separately as citations.

If the answer cannot be found in the context, say:

"I couldn't find that in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""
    )

    chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    async for token in chain.astream(
        {
            "context": context,
            "question": question,
        }
    ):

        if token:
            yield _sse(
                {
                    "type": "token",
                    "content": token,
                }
            )

    
    yield _sse(
        {
            "type": "done"
        }
    )


def list_documents(
    client: QdrantClient,
    collection_name: str,
) -> list:
    """
    Return one document entry per doc_id.

    Qdrant stores one point per chunk,
    so we group chunks by doc_id.
    """

    if not collection_exists(
        client,
        collection_name,
    ):
        return []

    documents = {}

    offset = None

    while True:

        records, next_offset = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for record in records:

            payload = record.payload

            doc_id = payload.get(
                "doc_id",
                "unknown",
            )

            # First chunk of this document.
            if doc_id not in documents:

                documents[doc_id] = {
                    "doc_id": doc_id,

                    "file_name": payload.get(
                        "file_name",
                        "unknown",
                    ),

                    "file_type": payload.get(
                        "file_type",
                        "unknown",
                    ),

                    "total_pages": payload.get(
                        "total_pages",
                        1,
                    ),

                    "upload_timestamp": payload.get(
                        "upload_timestamp",
                        "",
                    ),

                    "total_chunks": 0,

                    "status": "ready",
                }

            # Every Qdrant point represents
            # one chunk.
            documents[doc_id][
                "total_chunks"
            ] += 1

        if next_offset is None:
            break

        offset = next_offset

    return list(
        documents.values()
    )


def delete_document(
    doc_id: str,
    client: QdrantClient,
    collection_name: str,
) -> int:
    """
    Delete all chunks belonging to a document.

    Returns the number of deleted Qdrant points.
    """

    if not collection_exists(
        client,
        collection_name,
    ):
        return 0

    # Find all chunks having this doc_id.
    document_filter = Filter(
        must=[
            FieldCondition(
                key="doc_id",
                match=MatchValue(
                    value=doc_id
                ),
            )
        ]
    )

    # Count chunks first.
    count_result = client.count(
        collection_name=collection_name,
        count_filter=document_filter,
    )

    deleted_count = count_result.count

    # Delete all chunks.
    if deleted_count > 0:

        client.delete(
            collection_name=collection_name,
            points_selector=document_filter,
        )

    return deleted_count