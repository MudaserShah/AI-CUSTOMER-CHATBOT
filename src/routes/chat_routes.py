from fastapi import APIRouter

from src.agent.agent import app
from src.schemas.chat_schemas import ChatRequest, ChatResponse


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    result = app.invoke(
        {
            "customer_id": request.customer_id,
            "messages": [
                {
                    "role": "user",
                    "content": request.message,
                }
            ],
        },
        config={
            "configurable": {
                "thread_id": request.thread_id,
            }
        },
    )

    return {
        "thread_id": request.thread_id,
        "response": result["messages"][-1].content,
    }