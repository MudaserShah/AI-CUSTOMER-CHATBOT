from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    customer_id: str = Field(
        ...,
        description="Unique customer identifier",
    )

    thread_id: str = Field(
        ...,
        description="Conversation thread identifier",
    )

    message: str = Field(
        ...,
        min_length=1,
        description="Customer message",
    )


class ChatResponse(BaseModel):

    thread_id: str

    response: str