def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["message"] == "User created successfully"


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "securepass123"}
    client.post("/api/auth/register", json=payload)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400


def test_register_invalid_email(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 400


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "short"},
    )
    assert response.status_code == 400


def test_login_success(client, registered_user):
    response = client.post("/api/auth/login", json=registered_user)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401
