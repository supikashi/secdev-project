"""
Tests for owner-only authorization on suggestions.

Tests cover:
- Users can only update their own suggestions
- Users can only delete their own suggestions
- Users can read all suggestions
- Proper error messages for unauthorized access
"""


class TestOwnerOnlyAuthorization:
    """Test that users can only modify their own suggestions."""

    def test_user_can_create_own_suggestion(self, client, auth_headers):
        """Test that authenticated user can create a suggestion."""
        headers = auth_headers("user1", "pass12345")

        response = client.post(
            "/suggestions",
            headers=headers,
            json={"title": "My suggestion", "text": "This is my idea", "status": "new"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "My suggestion"
        assert response.json()["user_id"] == 1  # First user

    def test_user_can_update_own_suggestion(self, client, auth_headers):
        """Test that user can update their own suggestion."""
        headers = auth_headers("owner", "pass12345")

        response = client.post(
            "/suggestions",
            headers=headers,
            json={"title": "Original", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        response = client.put(
            f"/suggestions/{suggestion_id}",
            headers=headers,
            json={"title": "Updated", "text": "Updated text", "status": "reviewing"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"
        assert response.json()["status"] == "reviewing"

    def test_user_can_delete_own_suggestion(self, client, auth_headers):
        """Test that user can delete their own suggestion."""
        headers = auth_headers("owner", "pass12345")

        response = client.post(
            "/suggestions",
            headers=headers,
            json={"title": "To delete", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        response = client.delete(f"/suggestions/{suggestion_id}", headers=headers)

        assert response.status_code == 200
        assert "deleted" in response.json()["status"].lower()

        response = client.get(f"/suggestions/{suggestion_id}", headers=headers)
        assert response.status_code == 404

    def test_user_cannot_update_others_suggestion(self, client, auth_headers):
        """Test that user CANNOT update another user's suggestion."""
        headers1 = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "User1 idea", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        headers2 = auth_headers("user2", "pass12345")
        response = client.put(
            f"/suggestions/{suggestion_id}",
            headers=headers2,
            json={"title": "Hacked", "text": "Hacked text", "status": "approved"},
        )

        assert response.status_code == 403
        assert "forbidden" in response.json()["error"]["code"].lower()

    def test_user_cannot_delete_others_suggestion(self, client, auth_headers):
        """Test that user CANNOT delete another user's suggestion."""
        headers1 = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "User1 idea", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        # User 2 tries to delete it
        headers2 = auth_headers("user2", "pass12345")
        response = client.delete(f"/suggestions/{suggestion_id}", headers=headers2)

        assert response.status_code == 403
        assert "forbidden" in response.json()["error"]["code"].lower()

        response = client.get(f"/suggestions/{suggestion_id}", headers=headers1)
        assert response.status_code == 200

    def test_user_can_read_all_suggestions(self, client, auth_headers):
        """Test that users can read all suggestions (including others')."""
        headers1 = auth_headers("user1", "pass12345")
        client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "User1 idea", "text": "Text1", "status": "new"},
        )

        headers2 = auth_headers("user2", "pass12345")
        client.post(
            "/suggestions",
            headers=headers2,
            json={"title": "User2 idea", "text": "Text2", "status": "new"},
        )

        response = client.get("/suggestions", headers=headers1)
        assert response.status_code == 200
        suggestions = response.json()
        assert len(suggestions) >= 2

        response = client.get("/suggestions", headers=headers2)
        response = client.get("/suggestions", headers=headers2)
        assert response.status_code == 200
        suggestions = response.json()
        assert len(suggestions) >= 2

    def test_user_can_read_others_suggestion_details(self, client, auth_headers):
        """Test that users can read details of others' suggestions."""
        headers1 = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "User1 idea", "text": "Secret text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        headers2 = auth_headers("user2", "pass12345")
        response = client.get(f"/suggestions/{suggestion_id}", headers=headers2)

        assert response.status_code == 200
        assert response.json()["title"] == "User1 idea"
        assert response.json()["text"] == "Secret text"

    def test_unauthorized_user_cannot_create_suggestion(self, client):
        """Test that unauthenticated users cannot create suggestions."""
        response = client.post(
            "/suggestions",
            json={"title": "Unauthorized", "text": "Text", "status": "new"},
        )

        assert response.status_code == 401
        assert "auth_required" in response.json()["error"]["code"]

    def test_unauthorized_user_cannot_update_suggestion(self, client, auth_headers):
        """Test that unauthenticated users cannot update suggestions."""
        headers = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers,
            json={"title": "Original", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        response = client.put(
            f"/suggestions/{suggestion_id}",
            json={"title": "Hacked", "text": "Hacked", "status": "approved"},
        )

        assert response.status_code == 401

    def test_unauthorized_user_cannot_delete_suggestion(self, client, auth_headers):
        """Test that unauthenticated users cannot delete suggestions."""
        headers = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers,
            json={"title": "Original", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        response = client.delete(f"/suggestions/{suggestion_id}")

        assert response.status_code == 401

    def test_error_message_for_forbidden_update(self, client, auth_headers):
        """Test that forbidden update returns clear error message."""
        headers1 = auth_headers("user1", "pass12345")
        response = client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "User1 idea", "text": "Text", "status": "new"},
        )
        suggestion_id = response.json()["id"]

        headers2 = auth_headers("user2", "pass12345")
        response = client.put(
            f"/suggestions/{suggestion_id}",
            headers=headers2,
            json={"title": "Hacked", "text": "Text", "status": "new"},
        )

        assert response.status_code == 403
        error_message = response.json()["error"]["message"].lower()
        assert "owner" in error_message or "forbidden" in error_message

    def test_multiple_users_can_have_suggestions_with_same_title(
        self, client, auth_headers
    ):
        """Test that multiple users can create suggestions with same title."""
        headers1 = auth_headers("user1", "pass12345")
        response1 = client.post(
            "/suggestions",
            headers=headers1,
            json={"title": "Same title", "text": "Text1", "status": "new"},
        )
        assert response1.status_code == 200

        headers2 = auth_headers("user2", "pass12345")
        response2 = client.post(
            "/suggestions",
            headers=headers2,
            json={"title": "Same title", "text": "Text2", "status": "new"},
        )
        assert response2.status_code == 200

        assert response1.json()["id"] != response2.json()["id"]
        assert response1.json()["user_id"] != response2.json()["user_id"]
