from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import src.routes.chat_routes as chat_routes


app = FastAPI()
app.include_router(chat_routes.router)

client = TestClient(app)


def test_chat_route_success(monkeypatch):

    def fake_invoke(state, config):

        return {
            "messages": [
                AIMessage(
                    content="The status of order 12348 is Delivered."
                )
            ]
        }

    monkeypatch.setattr(
        chat_routes.app,
        "invoke",
        fake_invoke,
    )

    response = client.post(
        "/chat",
        json={
            "customer_id": "customer-002",
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
        json={
            "customer_id": "customer-002",
            "thread_id": "test-thread-002",
            "message": "",
        },
    )

    assert response.status_code == 422