import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.agent.agent import app
from src.auth.dependencies import get_current_customer_id
from src.database.errors import DatabaseError
from src.rate_limit import limiter
from src.schemas.chat_schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _invoke_agent(customer_id: str, message: str, thread_id: str):
    """Call the LLM/agent graph with a short retry for transient failures
    (e.g. the model provider briefly rate-limiting or timing out).
    Three attempts with short backoff; if it still fails, the caller
    decides how to respond to the client — see the except block below."""
    return app.invoke(
        {
            "customer_id": customer_id,
            "messages": [{"role": "user", "content": message}],
        },
        config={"configurable": {"thread_id": thread_id}},
    )


@router.post(
    "",
    response_model=ChatResponse,
)
@limiter.limit("20/minute")
def chat(
    request: Request,
    body: ChatRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    try:
        result = _invoke_agent(customer_id, body.message, body.thread_id)
    except DatabaseError:
        logger.exception("Database error while handling chat for customer_id=%s", customer_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble reaching our systems right now. Please try again shortly.",
        )
    except Exception:
        logger.exception("LLM/agent call failed for customer_id=%s", customer_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant is temporarily unavailable. Please try again in a moment.",
        )

    return {
        "thread_id": body.thread_id,
        "response": result["messages"][-1].content,
    }