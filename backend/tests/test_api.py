def test_login_and_current_user(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_can_create_user(client, admin_headers):
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "builder", "password": "BuilderPassword123!", "role": "member"},
    )
    assert response.status_code == 201
    assert response.json()["username"] == "builder"


def test_credential_secret_is_not_returned(client, admin_headers):
    response = client.post(
        "/api/credentials",
        headers=admin_headers,
        json={
            "name": "git-token",
            "type": "https-token",
            "username": "git",
            "secret": "top-secret",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "secret" not in body
    assert "encrypted_secret" not in body


def test_project_rejects_unsafe_git_scheme(client, admin_headers):
    response = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "name": "unsafe",
            "git_url": "file:///etc/passwd",
            "default_ref": "main",
            "vue_version": "3",
            "install_strategy": "none",
        },
    )
    assert response.status_code == 422


def test_project_crud(client, admin_headers):
    response = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "name": "demo",
            "git_url": "https://github.com/example/demo.git",
            "default_ref": "main",
            "vue_version": "3",
            "install_strategy": "npm-ci",
        },
    )
    assert response.status_code == 201
    project_id = response.json()["id"]
    listed = client.get("/api/projects", headers=admin_headers).json()
    assert any(project["id"] == project_id for project in listed)
