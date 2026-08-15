def test_login_and_current_user(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_login_sets_refresh_token_cookie(client):
    """登录成功后必须以 HttpOnly Cookie 下发 refresh_token，且不出现在响应体中。"""
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"}
    )
    assert response.status_code == 200
    assert "refresh_token" not in response.json()
    cookie_header = response.headers["set-cookie"]
    assert "refresh_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Path=/api/auth" in cookie_header
    # 测试环境为 development：不应带 Secure，SameSite 为 lax
    assert "Secure" not in cookie_header
    assert "SameSite=lax" in cookie_header


def test_refresh_with_cookie_returns_new_tokens(client):
    """携带登录下发的 refresh_token Cookie 请求刷新，应返回新令牌并轮换 Cookie。"""
    client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
    refresh_token = client.cookies.get("refresh_token")
    assert refresh_token

    response = client.post("/api/auth/refresh")
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["username"] == "admin"
    assert "refresh_token" not in body
    # 刷新成功后应重新下发 refresh_token Cookie（与登录同一秒内签发的 JWT 字节可能相同，
    # 故只断言重新下发且属性完整，不断言字节差异）
    new_cookie = response.headers["set-cookie"]
    assert "refresh_token=" in new_cookie
    assert "HttpOnly" in new_cookie
    assert "Path=/api/auth" in new_cookie


def test_refresh_without_cookie_returns_401(client):
    """未携带 refresh_token Cookie 请求刷新，应返回 401 且提示缺少刷新令牌。"""
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "缺少刷新令牌"


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
