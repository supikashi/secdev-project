from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_sample_suggestion():
    """Вспомогательная функция для создания предложения"""
    response = client.post(
        "/suggestions",
        json={
            "user_id": 1,
            "title": "Test Title",
            "text": "This is a test suggestion",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_post_suggestion_success():
    response = client.post(
        "/suggestions",
        json={
            "user_id": 1,
            "title": "New Suggestion",
            "text": "This is a valid suggestion text.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Suggestion"
    assert data["text"] == "This is a valid suggestion text."
    assert data["status"] == "new"
    assert "id" in data


def test_post_suggestion_validation_error_title():
    response = client.post(
        "/suggestions",
        json={
            "user_id": 1,
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
    updated = {
        "user_id": 1,
        "title": "Updated Title",
        "text": "Updated text content.",
        "status": "reviewed",
    }
    response = client.put(f"/suggestions/{suggestion['id']}", json=updated)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["text"] == "Updated text content."
    assert data["status"] == "reviewed"


def test_put_suggestion_not_found():
    response = client.put(
        "/suggestions/99999",
        json={
            "user_id": 1,
            "title": "Does not exist",
            "text": "No content",
            "status": "new",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_suggestion_success():
    suggestion = create_sample_suggestion()
    response = client.delete(f"/suggestions/{suggestion['id']}")
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}

    get_response = client.get(f"/suggestions/{suggestion['id']}")
    assert get_response.status_code == 404


def test_delete_suggestion_not_found():
    response = client.delete("/suggestions/99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_suggestions_filtering():
    client.delete("/suggestions/1")
    client.delete("/suggestions/2")

    client.post(
        "/suggestions",
        json={
            "user_id": 2,
            "title": "Suggestion A",
            "text": "Some text",
            "status": "new",
        },
    )
    client.post(
        "/suggestions",
        json={
            "user_id": 3,
            "title": "Suggestion B",
            "text": "Some other text",
            "status": "reviewed",
        },
    )

    response = client.get("/suggestions?status=reviewed")
    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "reviewed" for s in data)
