from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app

client = TestClient(app)


def setup_module(module):
    """Очистим in-memory состояния перед запуском тестов."""
    app_main._DB["items"].clear()
    app_main._DB["suggestions"].clear()
    if hasattr(app_main, "_TOKENS"):
        app_main._TOKENS.clear()
    if hasattr(app_main, "_RATE_LIMIT"):
        app_main._RATE_LIMIT.clear()


def login_headers(username: str = "alice", password: str = "alicepass"):
    resp = client.post(
        "/auth/login", params={"username": username, "password": password}
    )
    assert resp.status_code == 200, f"login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_rate_limit():
    username = "alice"
    wrong_password = "badpass"

    # ensure counter empty
    app_main._RATE_LIMIT.pop(username, None)

    # first 5 attempts -> 401 (invalid credentials)
    for i in range(app_main.RATE_LIMIT_ATTEMPTS):
        r = client.post(
            "/auth/login", params={"username": username, "password": wrong_password}
        )
        assert (
            r.status_code == 401
        ), f"expected 401 on attempt {i+1}, got {r.status_code} / {r.text}"
        body = r.json()
        assert body["error"]["code"] == "invalid_credentials"

    # 6th attempt -> 429 too many requests
    r6 = client.post(
        "/auth/login", params={"username": username, "password": wrong_password}
    )
    assert (
        r6.status_code == 429
    ), f"expected 429 on 6th attempt, got {r6.status_code} / {r6.text}"
    body6 = r6.json()
    assert body6["error"]["code"] == "too_many_requests"

    # cleanup for other tests
    app_main._RATE_LIMIT.pop(username, None)
