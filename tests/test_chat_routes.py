from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import src.routes.chat_routes as chat_routes
from src.auth.jwt_utils import create_access_token
from src.rate_limit import limiter

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(chat_routes.router)

client = TestClient(app)

TEST_CUSTOMER_ID = "customer-002"
AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token(TEST_CUSTOMER_ID)}"}


def test_chat_route_success(monkeypatch):

    def fake_invoke_agent(customer_id, message, thread_id):
        # customer_id must come from the authenticated token, never
        # from client input — this is the actual security guarantee
        # Phase 1 added, so the test checks it directly.
        assert customer_id == TEST_CUSTOMER_ID

        return {
            "messages": [
                AIMessage(
                    content="The status of order 12348 is Delivered."
                )
            ]
        }

    monkeypatch.setattr(chat_routes, "_invoke_agent", fake_invoke_agent)

    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={
            "thread_id": "test-thread-001",
            "message": "What is the status of order 12348?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["thread_id"] == "test-thread-001"
    assert data["response"] == "The status of order 12348 is Delivered."


def test_chat_route_empty_message():

    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={
            "thread_id": "test-thread-002",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_chat_route_missing_auth():
    # No Authorization header at all — must be rejected before the
    # request ever reaches the agent.
    response = client.post(
        "/chat",
        json={
            "thread_id": "test-thread-003",
            "message": "hello",
        },
    )

    assert response.status_code == 401


def test_chat_route_invalid_token():
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer not-a-real-token"},
        json={
            "thread_id": "test-thread-004",
            "message": "hello",
        },
    )

    assert response.status_code == 401
