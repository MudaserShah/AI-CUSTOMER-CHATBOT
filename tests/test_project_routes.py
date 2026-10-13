import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.routes.project_routes as project_routes

app = FastAPI()
app.include_router(project_routes.router)

client = TestClient(app)


def test_list_projects():
    response = client.get("/projects")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    assert any(p["id"] == "technest-default" for p in projects)


def test_get_project_technest():
    response = client.get("/projects/technest-default")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "technest-default"
    assert data["slug"] == "technest"


def test_create_and_update_project():
    unique_name = f"Test Store {uuid.uuid4().hex[:6]}"
    # Create project
    create_res = client.post(
        "/projects",
        json={
            "name": unique_name,
            "widget_title": "Support Bot",
            "widget_greeting": "How may I help you?",
            "primary_color": "#10b981",
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    project_id = created["id"]
    assert created["name"] == unique_name
    assert created["widget_title"] == "Support Bot"

    # Update project
    update_res = client.patch(
        f"/projects/{project_id}",
        json={
            "system_prompt": "You are a friendly shoe store agent.",
            "primary_color": "#ef4444",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["system_prompt"] == "You are a friendly shoe store agent."
    assert updated["primary_color"] == "#ef4444"
