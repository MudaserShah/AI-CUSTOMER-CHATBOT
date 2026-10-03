from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    # customer_id intentionally removed — it is derived from the
    # authenticated JWT (see src/auth/dependencies.py), never from
    # client input. Trusting a client-supplied customer_id let any
    # caller read or act as any other customer.

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