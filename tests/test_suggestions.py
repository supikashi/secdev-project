from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app

client = TestClient(app)


def setup_module(module):
    """Очистить in-memory хранилища перед запуском тестов модуля."""
    app_main._DB["items"].clear()
    app_main._DB["suggestions"].clear()
    # если переменные существуют — очистим их
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


def create_sample_suggestion():
    """Вспомогательная функция для создания предложения от имени alice"""
    headers = login_headers("alice", "alicepass")
    response = client.post(
        "/suggestions",
        headers=headers,
        json={
            "title": "Test Title",
            "text": "This is a test suggestion",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_post_suggestion_success():
    headers = login_headers("alice", "alicepass")
    response = client.post(
        "/suggestions",
        headers=headers,
        json={
            "title": "New Suggestion",
            "text": "This is a valid suggestion text.",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "New Suggestion"
    assert data["text"] == "This is a valid suggestion text."
    assert data["status"] == "new"
    assert "id" in data
    assert data["user_id"] == 1  # alice


def test_post_suggestion_validation_error_title():
    headers = login_headers("alice", "alicepass")
    response = client.post(
        "/suggestions",
        headers=headers,
        json={
            "title": "",
            "text": "Valid text.",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_suggestion_by_id_success():
    suggestion = create_sample_suggestion()
    response = client.get(f"/suggestions/{suggestion['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == suggestion["id"]
    assert data["title"] == suggestion["title"]


def test_get_suggestion_not_found():
    response = client.get("/suggestions/99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_put_suggestion_success():
    suggestion = create_sample_suggestion()
    headers = login_headers("alice", "alicepass")
    updated = {
        "title": "Updated Title",
        "text": "Updated text content.",
        "status": "reviewed",
    }
    response = client.put(
        f"/suggestions/{suggestion['id']}", headers=headers, json=updated
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["text"] == "Updated text content."
    assert data["status"] == "reviewed"


def test_put_suggestion_not_found():
    headers = login_headers("alice", "alicepass")
    response = client.put(
        "/suggestions/99999",
        headers=headers,
        json={
            "title": "Does not exist",
            "text": "No content",
            "status": "new",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_suggestion_success():
    suggestion = create_sample_suggestion()
    headers = login_headers("alice", "alicepass")
    response = client.delete(f"/suggestions/{suggestion['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}

    get_response = client.get(f"/suggestions/{suggestion['id']}")
    assert get_response.status_code == 404


def test_delete_suggestion_not_found():
    headers = login_headers("alice", "alicepass")
    response = client.delete("/suggestions/99999", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_suggestions_filtering():
    headers_alice = login_headers("alice", "alicepass")
    headers_bob = login_headers("bob", "bobpass")

    resp1 = client.post(
        "/suggestions",
        headers=headers_alice,
        json={"title": "Suggestion A", "text": "Some text", "status": "new"},
    )
    assert resp1.status_code == 200, resp1.text

    resp2 = client.post(
        "/suggestions",
        headers=headers_bob,
        json={"title": "Suggestion B", "text": "Some other text", "status": "reviewed"},
    )
    assert resp2.status_code == 200, resp2.text

    response = client.get("/suggestions?status=reviewed")
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "reviewed" for s in data)
    assert any(s["title"] == "Suggestion B" for s in data)


def test_user_cannot_modify_others_suggestion():
    # alice создаёт предложение
    headers_alice = login_headers("alice", "alicepass")
    resp = client.post(
        "/suggestions",
        headers=headers_alice,
        json={"title": "Alice's Suggestion", "text": "Alice text"},
    )
    assert resp.status_code == 200, resp.text
    suggestion = resp.json()
    sid = suggestion["id"]
    assert suggestion["user_id"] == 1

    # bob логинится и пытается обновить предложение alice -> 403
    headers_bob = login_headers("bob", "bobpass")
    update_resp = client.put(
        f"/suggestions/{sid}",
        headers=headers_bob,
        json={"title": "Hacked", "text": "Hacked", "status": "reviewed"},
    )
    assert update_resp.status_code == 403
    assert update_resp.json()["error"]["code"] == "forbidden"

    # bob пытается удалить -> 403
    del_resp = client.delete(f"/suggestions/{sid}", headers=headers_bob)
    assert del_resp.status_code == 403
    assert del_resp.json()["error"]["code"] == "forbidden"

    # владелец (alice) может удалить успешно
    del_resp_owner = client.delete(f"/suggestions/{sid}", headers=headers_alice)
    assert del_resp_owner.status_code == 200
    assert del_resp_owner.json() == {"status": "deleted"}
