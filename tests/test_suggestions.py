"""Basic tests for suggestions CRUD operations."""


def test_create_suggestion_success(client, auth_headers):
    """Test successful suggestion creation."""
    headers = auth_headers()
    response = client.post(
        "/suggestions",
        headers=headers,
        json={"title": "Test suggestion", "text": "Test text"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test suggestion"
    assert data["status"] == "new"


def test_get_all_suggestions(client, auth_headers):
    """Test retrieving all suggestions."""
    headers = auth_headers()
    client.post(
        "/suggestions",
        headers=headers,
        json={"title": "Suggestion 1", "text": "Text 1"},
    )
    client.post(
        "/suggestions",
        headers=headers,
        json={"title": "Suggestion 2", "text": "Text 2"},
    )

    response = client.get("/suggestions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_update_suggestion_success(client, auth_headers):
    """Test updating own suggestion."""
    headers = auth_headers()
    create_resp = client.post(
        "/suggestions",
        headers=headers,
        json={"title": "Original", "text": "Original text"},
    )
    suggestion_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/suggestions/{suggestion_id}",
        headers=headers,
        json={"title": "Updated", "text": "Updated text"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated"


def test_delete_suggestion_success(client, auth_headers):
    """Test deleting own suggestion."""
    headers = auth_headers()
    create_resp = client.post(
        "/suggestions",
        headers=headers,
        json={"title": "To delete", "text": "Will be deleted"},
    )
    suggestion_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/suggestions/{suggestion_id}", headers=headers)
    assert delete_resp.status_code == 200

    get_resp = client.get("/suggestions", headers=headers)
    assert suggestion_id not in [s["id"] for s in get_resp.json()]


def test_create_suggestion_invalid_status(client, auth_headers):
    """Test that invalid status is rejected."""
    headers = auth_headers()
    response = client.post(
        "/suggestions",
        headers=headers,
        json={"title": "Test", "text": "Test", "status": "invalid_status"},
    )
    assert response.status_code == 422
