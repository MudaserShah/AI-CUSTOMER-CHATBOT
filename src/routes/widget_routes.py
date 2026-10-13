import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.database.errors import DatabaseError
from src.database.project_repository import ProjectRepository
from src.rate_limit import limiter
from src.routes.chat_routes import _invoke_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/widget", tags=["Widget"])
project_repo = ProjectRepository()


class WidgetConfigRequest(BaseModel):
    project_id: Optional[str] = None
    api_key: Optional[str] = None


class WidgetConfigResponse(BaseModel):
    project_id: str
    name: str
    slug: str
    widget_title: str
    widget_greeting: str
    primary_color: str


class WidgetChatRequest(BaseModel):
    thread_id: str = Field(..., description="Conversation thread identifier")
    message: str = Field(..., min_length=1, description="Visitor message")
    project_id: Optional[str] = Field(default="technest-default", description="Project identifier")
    api_key: Optional[str] = Field(default=None, description="Public project API key")
    visitor_id: Optional[str] = Field(default=None, description="Anonymous or identified visitor ID")
    customer_email: Optional[str] = Field(default=None, description="Logged-in customer email from client website")
    customer_name: Optional[str] = Field(default=None, description="Logged-in customer name from client website")


class WidgetChatResponse(BaseModel):
    thread_id: str
    response: str
    project_id: str


@router.get("/config", response_model=WidgetConfigResponse)
def get_widget_config(project_id: Optional[str] = None, api_key: Optional[str] = None):
    project = None
    if api_key:
        project = project_repo.get_project_by_api_key(api_key)
    elif project_id:
        project = project_repo.get_project(project_id)
    else:
        project = project_repo.get_project("technest-default")

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found. Please verify your project_id or api_key.",
        )

    return {
        "project_id": project["id"],
        "name": project["name"],
        "slug": project["slug"],
        "widget_title": project["widget_title"],
        "widget_greeting": project["widget_greeting"],
        "primary_color": project["primary_color"],
    }


from src.database.repository import CustomerRepository
customer_repo = CustomerRepository()


def _format_clean_response(text: str) -> str:
    if not text:
        return ""
    # Ensure bullets start on clean new lines
    t = re.sub(r"([^\n])\s+[-•*]\s+", r"\1\n• ", text)
    # Ensure bold section headers start on new paragraph
    t = re.sub(r"([.!?:])\s*(\*\*[A-Z][A-Za-z0-9\s\-/]+?:\*\*)", r"\1\n\n\2", t)
    # Ensure closing sentences start on new paragraph
    t = re.sub(r"(\))\s+(This order|The order|Please|Would you|Is there|Feel free|You can)", r"\1\n\n\2", t)
    return t.strip()


@router.post("/chat", response_model=WidgetChatResponse)
@limiter.limit("30/minute")
def widget_chat(request: Request, body: WidgetChatRequest):
    # Resolve project
    project = None
    if body.api_key:
        project = project_repo.get_project_by_api_key(body.api_key)
    elif body.project_id:
        project = project_repo.get_project(body.project_id)

    if not project:
        project = project_repo.get_project("technest-default")

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    resolved_project_id = project["id"]

    # Natural identity resolution: use email if available
    if body.customer_email:
        record = customer_repo.get_customer_by_email(body.customer_email)
        if record:
            visitor_id = record[1]
        else:
            safe_slug = re.sub(r"[^\w-]", "", body.customer_email.split("@")[0])[:12]
            guest = customer_repo.get_or_create_customer(
                customer_id=f"cust-{safe_slug}",
                name=body.customer_name or "Guest",
                email=body.customer_email,
            )
            visitor_id = guest[1]
    else:
        visitor_id = body.visitor_id or f"visitor-{body.thread_id[:16]}"

    try:
        result = _invoke_agent(
            customer_id=visitor_id,
            message=body.message,
            thread_id=body.thread_id,
            project_id=resolved_project_id,
        )
    except DatabaseError:
        logger.exception("Database error while handling widget chat for project=%s", resolved_project_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble reaching our systems right now. Please try again shortly.",
        ) from None
    except Exception:
        logger.exception("Agent invocation failed for widget chat project=%s", resolved_project_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant is temporarily unavailable. Please try again in a moment.",
        ) from None

    raw_response = result["messages"][-1].content
    cleaned_response = _format_clean_response(raw_response)

    return {
        "thread_id": body.thread_id,
        "response": cleaned_response,
        "project_id": resolved_project_id,
    }
