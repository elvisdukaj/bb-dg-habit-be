import pytest


@pytest.fixture
def habit_payload():
    return {"title": "Drink water", "frequency": "daily"}


def test_create_habit(client, auth_headers, habit_payload):
    response = client.post("/api/habits", json=habit_payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == habit_payload["title"]
    assert body["frequency"] == habit_payload["frequency"]
    assert "id" in body
    assert "user_id" in body


def test_create_habit_unauthorized(client, habit_payload):
    response = client.post("/api/habits", json=habit_payload)
    assert response.status_code == 401


def test_create_habit_invalid_frequency(client, auth_headers):
    response = client.post(
        "/api/habits",
        json={"title": "Exercise", "frequency": "monthly"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_habit_empty_title(client, auth_headers):
    response = client.post(
        "/api/habits",
        json={"title": "", "frequency": "daily"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_list_habits(client, auth_headers, habit_payload):
    client.post("/api/habits", json=habit_payload, headers=auth_headers)
    client.post(
        "/api/habits",
        json={"title": "Exercise", "frequency": "weekly"},
        headers=auth_headers,
    )
    response = client.get("/api/habits", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_habits_empty(client, auth_headers):
    response = client.get("/api/habits", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_habit(client, auth_headers, habit_payload):
    created = client.post("/api/habits", json=habit_payload, headers=auth_headers).json()
    response = client.get(f"/api/habits/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_habit_not_found(client, auth_headers):
    response = client.get("/api/habits/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_update_habit(client, auth_headers, habit_payload):
    created = client.post("/api/habits", json=habit_payload, headers=auth_headers).json()
    update = {"title": "Read 10 pages", "frequency": "weekly"}
    response = client.put(f"/api/habits/{created['id']}", json=update, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Read 10 pages"
    assert body["frequency"] == "weekly"


def test_update_habit_not_found(client, auth_headers):
    response = client.put(
        "/api/habits/nonexistent-id",
        json={"title": "Something", "frequency": "daily"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_delete_habit(client, auth_headers, habit_payload):
    created = client.post("/api/habits", json=habit_payload, headers=auth_headers).json()
    response = client.delete(f"/api/habits/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    get_response = client.get(f"/api/habits/{created['id']}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_habit_not_found(client, auth_headers):
    response = client.delete("/api/habits/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_user_cannot_access_other_users_habit(client, habit_payload):
    client.post(
        "/api/auth/register",
        json={"email": "user1@example.com", "password": "password123"},
    )
    client.post(
        "/api/auth/register",
        json={"email": "user2@example.com", "password": "password123"},
    )

    login1 = client.post(
        "/api/auth/login",
        json={"email": "user1@example.com", "password": "password123"},
    )
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    login2 = client.post(
        "/api/auth/login",
        json={"email": "user2@example.com", "password": "password123"},
    )
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    created = client.post("/api/habits", json=habit_payload, headers=headers1).json()

    response = client.get(f"/api/habits/{created['id']}", headers=headers2)
    assert response.status_code == 404
