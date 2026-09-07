from typing import Annotated, List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response, StreamingResponse

from rag.api_logic import (
    get_documents,
    get_file_markdown,
    get_original_file,
    health,
    query,
    query_stream_endpoint,
    remove_document,
    upload_documents,
)

from rag.schemas import (
    DeleteResponse,
    DocumentListResponse,
    FileContentResponse,
    QueryResponse,
    UploadFilesResponse,
    QueryRequest
)


router = APIRouter()


# ─── Documents ────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadFilesResponse,
    tags=["Documents"],
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "One or more files: PDF, DOCX, MD, CSV, TXT"
                            }
                        },
                        "required": ["files"]
                    }
                }
            }
        }
    }
)
async def upload_files(
    files: Annotated[
        List[UploadFile],
        File(
            description="One or more files: PDF, DOCX, MD, CSV, TXT"
        ),
    ],
) -> UploadFilesResponse:

    return await upload_documents(files)

# Seedha api function ko endpoint handler assign kar diya taake Depends chale
router.add_api_route(
    "/documents",
    endpoint=get_documents,
    methods=["GET"],
    response_model=DocumentListResponse,
    tags=["Documents"],
)

router.add_api_route(
    "/documents/{doc_id}",
    endpoint=remove_document,
    methods=["DELETE"],
    response_model=DeleteResponse,
    tags=["Documents"],
)


# ─── RAG ──────────────────────────────────────────────────────────────────────

router.add_api_route(
    "/query",
    endpoint=query,
    methods=["POST"],
    response_model=QueryResponse,
    tags=["RAG"],
)

router.add_api_route(
    "/query/stream",
    endpoint=query_stream_endpoint,
    methods=["POST"],
    response_class=StreamingResponse,
    tags=["RAG"],
    summary="Query Stream Endpoint",
)


# ─── Files & Health ───────────────────────────────────────────────────────────

@router.get("/files/{doc_id}/markdown", response_model=FileContentResponse, tags=["Files"])
def get_markdown_route(doc_id: str):
    return get_file_markdown(doc_id)

@router.get("/files/{doc_id}/original", tags=["Files"])
def get_original_route(doc_id: str):
    return get_original_file(doc_id)

@router.get("/health", tags=["Health"])
def health_route() -> dict:
    return health()