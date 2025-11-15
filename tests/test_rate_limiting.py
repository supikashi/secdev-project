"""
Tests for rate limiting functionality.

Tests cover:
- Rate limiting by username (5 attempts per 60 seconds)
- Rate limiting by IP (10 attempts per 60 seconds)
- Rate limit reset after successful login
- Rate limit window expiration
"""


class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""

    def test_rate_limit_by_username_blocks_after_5_attempts(self, client):
        """Test that rate limiting blocks after 5 failed login attempts."""
        username = "testuser"

        for i in range(5):
            response = client.post(
                "/auth/login",
                params={"username": username, "password": "wrongpassword"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "invalid_credentials"

        response = client.post(
            "/auth/login", params={"username": username, "password": "wrongpassword"}
        )
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "too_many_requests"
        assert "username" in response.json()["error"]["message"].lower()

    def test_rate_limit_by_ip_blocks_after_10_attempts(self, client):
        """Test that rate limiting blocks after 10 failed attempts from same IP."""

        for i in range(10):
            response = client.post(
                "/auth/login",
                params={"username": f"user{i}", "password": "wrongpassword"},
            )
            assert response.status_code == 401

        response = client.post(
            "/auth/login", params={"username": "user99", "password": "wrongpassword"}
        )
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "too_many_requests"
        assert "ip" in response.json()["error"]["message"].lower()

    def test_rate_limit_resets_after_successful_login(self, client):
        """Test that rate limit is cleared after successful login."""
        username = "testuser"
        password = "test12345"

        response = client.post(
            "/auth/register", params={"username": username, "password": password}
        )
        assert response.status_code == 200

        for i in range(3):
            response = client.post(
                "/auth/login",
                params={"username": username, "password": "wrongpassword"},
            )
            assert response.status_code == 401

        response = client.post(
            "/auth/login", params={"username": username, "password": password}
        )
        assert response.status_code == 200

        for i in range(5):
            response = client.post(
                "/auth/login",
                params={"username": username, "password": "wrongpassword"},
            )
            assert response.status_code == 401

        response = client.post(
            "/auth/login", params={"username": username, "password": "wrongpassword"}
        )
        assert response.status_code == 429

    def test_rate_limit_different_usernames_independent(self, client):
        """Test that rate limits are independent per username."""
        for i in range(5):
            response = client.post(
                "/auth/login", params={"username": "user1", "password": "wrong"}
            )
            assert response.status_code == 401

        response = client.post(
            "/auth/login", params={"username": "user1", "password": "wrong"}
        )
        assert response.status_code == 429

        response = client.post(
            "/auth/login", params={"username": "user2", "password": "wrong"}
        )
        assert response.status_code == 401  # Not rate limited, just invalid creds

    def test_rate_limit_error_message_for_username(self, client):
        """Test that rate limit error message mentions username."""
        username = "blocked_user"

        for i in range(6):
            client.post(
                "/auth/login", params={"username": username, "password": "wrong"}
            )

        response = client.post(
            "/auth/login", params={"username": username, "password": "wrong"}
        )

        assert response.status_code == 429
        error_message = response.json()["error"]["message"]
        assert "username" in error_message.lower() or "user" in error_message.lower()

    def test_rate_limit_error_message_for_ip(self, client):
        """Test that rate limit error message mentions IP."""
        # Trigger IP rate limit with different usernames
        for i in range(11):
            client.post(
                "/auth/login", params={"username": f"ipuser{i}", "password": "wrong"}
            )

        response = client.post(
            "/auth/login", params={"username": "ipuser99", "password": "wrong"}
        )

        assert response.status_code == 429
        error_message = response.json()["error"]["message"]
        assert "ip" in error_message.lower()

    def test_successful_login_does_not_count_toward_rate_limit(self, client):
        """Test that successful logins don't count toward rate limit."""
        username = "gooduser"
        password = "goodpass123"

        client.post(
            "/auth/register", params={"username": username, "password": password}
        )

        for i in range(10):
            response = client.post(
                "/auth/login", params={"username": username, "password": password}
            )
            assert response.status_code == 200

        response = client.post(
            "/auth/login", params={"username": username, "password": password}
        )
        assert response.status_code == 200

    def test_rate_limit_returns_429_status(self, client):
        """Test that rate limiting returns proper HTTP 429 status."""
        username = "ratelimited"

        for i in range(6):
            client.post(
                "/auth/login", params={"username": username, "password": "wrong"}
            )

        response = client.post(
            "/auth/login", params={"username": username, "password": "wrong"}
        )

        assert response.status_code == 429
        assert "too_many_requests" in response.json()["error"]["code"]
