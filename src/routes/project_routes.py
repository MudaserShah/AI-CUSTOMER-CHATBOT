import logging
import os
import re
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.database.project_repository import ProjectRepository
from src.rag.api_logic import app_state
from src.rag.config import settings
from src.rag.file_loaders import is_supported
from src.rag.rag_service import (
    compute_doc_id,
    delete_document,
    index_document,
    list_documents,
)
from src.rag.schemas import DeleteResponse, DocumentListResponse, FileUploadResult, UploadFilesResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects (SaaS)"])
project_repo = ProjectRepository()


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project or business name")
    slug: Optional[str] = Field(default=None, description="URL-friendly slug (auto-generated if omitted)")
    system_prompt: Optional[str] = Field(default=None, description="Custom AI persona and instructions")
    llm_model: Optional[str] = Field(default=None, description="Override LLM model name")
    widget_title: str = Field(default="AI Support Assistant", description="Title in widget header")
    widget_greeting: str = Field(default="Hello! How can I help you today?", description="Initial greeting message")
    primary_color: str = Field(default="#2563eb", description="Hex color code for widget")


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = None
    widget_title: Optional[str] = None
    widget_greeting: Optional[str] = None
    primary_color: Optional[str] = None


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(body: CreateProjectRequest):
    slug = body.slug or _slugify(body.name)
    existing = project_repo.get_project_by_slug(slug)
    if existing:
        import uuid
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    created = project_repo.create_project(
        name=body.name,
        slug=slug,
        system_prompt=body.system_prompt,
        llm_model=body.llm_model,
        widget_title=body.widget_title,
        widget_greeting=body.widget_greeting,
        primary_color=body.primary_color,
    )
    return created


@router.get("")
def list_projects():
    return project_repo.list_projects()


@router.get("/{project_id}")
def get_project(project_id: str):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}")
def update_project(project_id: str, body: UpdateProjectRequest):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updated = project_repo.update_project(
        project_id=project_id,
        name=body.name,
        system_prompt=body.system_prompt,
        llm_model=body.llm_model,
        widget_title=body.widget_title,
        widget_greeting=body.widget_greeting,
        primary_color=body.primary_color,
    )
    return updated


# ---------------- Project Knowledge Base (RAG) ---------------- #

@router.post("/{project_id}/documents/upload", response_model=UploadFilesResponse)
async def upload_project_documents(
    project_id: str,
    files: Annotated[List[UploadFile], File(description="One or more files: PDF, DOCX, MD, CSV, TXT")],
):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results: List[FileUploadResult] = []

    for upload in files:
        file_name = upload.filename or "unknown"
        ext = Path(file_name).suffix.lower().lstrip(".")

        if not is_supported(file_name):
            results.append(
                FileUploadResult(
                    file_name=file_name,
                    doc_id=compute_doc_id(file_name),
                    file_type=ext,
                    status="error",
                    message="Unsupported file type",
                    error=f"Accepted: PDF, DOCX, MD, CSV, TXT. Got: .{ext}",
                )
            )
            continue

        content = await upload.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.max_upload_size_mb:
            results.append(
                FileUploadResult(
                    file_name=file_name,
                    doc_id=compute_doc_id(file_name),
                    file_type=ext,
                    status="error",
                    message="File too large",
                    error=f"File is {size_mb:.1f} MB. Max: {settings.max_upload_size_mb} MB",
                )
            )
            continue

        doc_id = compute_doc_id(f"{project_id}_{file_name}")
        project_upload_dir = os.path.join(settings.uploads_dir, project_id)
        os.makedirs(project_upload_dir, exist_ok=True)
        tmp_path = os.path.join(project_upload_dir, f"{doc_id}_{file_name}")

        with open(tmp_path, "wb") as f:
            f.write(content)

        try:
            logger.info("Indexing for project %s: %s", project_id, file_name)
            index_document(
                file_path=tmp_path,
                file_name=file_name,
                client=app_state["qdrant_client"],
                embeddings=app_state["embeddings"],
                collection_name=settings.qdrant_collection,
                uploads_dir=settings.uploads_dir,
                markdown_dir=settings.markdown_dir,
                project_id=project_id,
            )
            results.append(
                FileUploadResult(
                    file_name=file_name,
                    doc_id=doc_id,
                    file_type=ext,
                    status="ready",
                    message=f"'{file_name}' indexed successfully for project '{project['name']}'.",
                )
            )
        except Exception as e:
            logger.error("Indexing failed for %s (project %s): %s", file_name, project_id, e)
            results.append(
                FileUploadResult(
                    file_name=file_name,
                    doc_id=doc_id,
                    file_type=ext,
                    status="error",
                    message="Indexing failed",
                    error=str(e),
                )
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Purane return statement (line 198) ko is se tabdeel karein:
    return UploadFilesResponse(
    files=results,
    results=results,  # Kuch models 'files' ki jagah ya sath 'results' maangte hain
    total_files=len(results),
    successful=len([f for f in results if f.error is None]),
    failed=len([f for f in results if f.error is not None])
)



@router.get("/{project_id}/documents", response_model=DocumentListResponse)
def list_project_documents(project_id: str):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = list_documents(
        client=app_state["qdrant_client"],
        collection_name=settings.qdrant_collection,
        project_id=project_id,
    )
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{project_id}/documents/{doc_id}", response_model=DeleteResponse)
def delete_project_document(project_id: str, doc_id: str):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted_count = delete_document(
        doc_id=doc_id,
        client=app_state["qdrant_client"],
        collection_name=settings.qdrant_collection,
        project_id=project_id,
    )
    return DeleteResponse(
        doc_id=doc_id,
        deleted_chunks=deleted_count,
        message=f"Deleted {deleted_count} chunk(s) from project '{project['name']}'.",
    )


# ---------------- Project Tools / Webhooks ---------------- #

from src.database.project_tool_repository import ProjectToolRepository
project_tool_repo = ProjectToolRepository()


class CreateToolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Tool identifier (e.g. check_order)")
    description: str = Field(..., min_length=5, description="Clear description for the LLM of what this tool does")
    method: str = Field(default="GET", description="HTTP method: GET, POST, PUT, DELETE")
    endpoint_url: str = Field(..., description="API endpoint URL (can include placeholders like {order_id})")
    headers: Optional[dict] = Field(default=None, description="Optional custom headers (API keys, Authorization)")
    parameters_schema: Optional[dict] = Field(default=None, description="JSON Schema for parameters the tool expects")


@router.post("/{project_id}/tools", status_code=status.HTTP_201_CREATED)
def create_project_tool(project_id: str, body: CreateToolRequest):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tool = project_tool_repo.create_tool(
        project_id=project_id,
        name=body.name,
        description=body.description,
        method=body.method,
        endpoint_url=body.endpoint_url,
        headers=body.headers,
        parameters_schema=body.parameters_schema,
    )
    return tool


@router.get("/{project_id}/tools")
def list_project_tools(project_id: str):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project_tool_repo.list_tools_for_project(project_id)


@router.delete("/{project_id}/tools/{tool_id}")
def delete_project_tool(project_id: str, tool_id: str):
    project = project_repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted = project_tool_repo.delete_tool(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "ok", "message": "Tool deleted successfully"}

