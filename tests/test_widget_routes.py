from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import src.routes.widget_routes as widget_routes
from src.rate_limit import limiter

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(widget_routes.router)

client = TestClient(app)


def test_widget_config_default():
    response = client.get("/widget/config?project_id=technest-default")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "technest-default"
    assert "TechNest" in data["name"]
    assert "widget_title" in data
    assert "widget_greeting" in data


def test_widget_config_not_found():
    response = client.get("/widget/config?project_id=non_existent_project_xyz")
    assert response.status_code == 404


def test_widget_chat_success(monkeypatch):
    def fake_invoke_agent(customer_id, message, thread_id, project_id="technest-default"):
        return {
            "messages": [
                AIMessage(content="Hello from widget assistant!")
            ]
        }

    monkeypatch.setattr(widget_routes, "_invoke_agent", fake_invoke_agent)

    response = client.post(
        "/widget/chat",
        json={
            "thread_id": "widget-session-abc",
            "message": "Hello!",
            "project_id": "technest-default",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "widget-session-abc"
    assert data["response"] == "Hello from widget assistant!"
    assert data["project_id"] == "technest-default"
