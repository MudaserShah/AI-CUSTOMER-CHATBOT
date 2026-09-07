from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class Citation(BaseModel):
    """One source chunk used to generate the answer. Contains everything needed
    for the frontend to open the exact location in the original document"""
    file_name: str
    page_number:  Optional[int] = None
    row_number :  Optional[int] = None
    chunk_index: int
    chunk_text: str
    relevance_score: float
    doc_id: str
    is_table: bool = False

class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20, description="Amounts of chunks to retrieve")

class QueryResponse(BaseModel):
    answer: str
    references: List[Citation]

class FileUploadResult(BaseModel):
    file_name: str
    doc_id: str
    file_type: str
    status: str
    message: str
    error: Optional[str] = None

class UploadFilesResponse(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: List[FileUploadResult]

class DocumentStatus(str, Enum):
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"

class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    total_chunks: int
    total_pages: int
    upload_timestamp: str
    status: DocumentStatus = DocumentStatus.READY

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int

class DeleteResponse(BaseModel):
    doc_id: str
    status: str
    message: str

class FileContentResponse(BaseModel):
    """Response for GET /files/{doc_id}/markdown — used by the file viewer."""
    doc_id: str
    file_name: str
    file_type: str
    content: str
    total_pages: int