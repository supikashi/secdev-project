"""
Tests for SQL Injection prevention.

Tests cover:
- Username validation against SQL injection patterns
- Parameterized queries in all database operations
- Input sanitization
"""


class TestSQLInjection:
    """Test SQL injection prevention in all endpoints."""

    def test_sql_injection_in_register_username_with_quote(self, client):
        """Test SQL injection with single quote in username."""
        response = client.post(
            "/auth/register",
            params={"username": "admin' OR '1'='1", "password": "test12345"},
        )
        assert response.status_code == 422
        assert "validation_error" in response.json()["error"]["code"]
        # Message should mention alphanumeric, letters, numbers, or underscores
        message = response.json()["error"]["message"].lower()
        assert any(
            word in message
            for word in ["alphanumeric", "letters", "numbers", "underscores"]
        )

    def test_sql_injection_in_register_username_with_comment(self, client):
        """Test SQL injection with SQL comment."""
        response = client.post(
            "/auth/register", params={"username": "admin'--", "password": "test12345"}
        )
        assert response.status_code == 422
        assert "validation_error" in response.json()["error"]["code"]

    def test_sql_injection_in_register_username_with_semicolon(self, client):
        """Test SQL injection with semicolon."""
        response = client.post(
            "/auth/register",
            params={"username": "admin;DROP TABLE users", "password": "test12345"},
        )
        assert response.status_code == 422
        assert "validation_error" in response.json()["error"]["code"]

    def test_sql_injection_with_union_select(self, client):
        """Test SQL injection with UNION SELECT."""
        response = client.post(
            "/auth/register",
            params={"username": "admin' UNION SELECT", "password": "test12345"},
        )
        assert response.status_code == 422

    def test_sql_injection_with_drop_keyword(self, client):
        """Test SQL injection with DROP keyword."""
        response = client.post(
            "/auth/register",
            params={"username": "user_DROP_table", "password": "test12345"},
        )
        assert response.status_code == 422
        assert "invalid" in response.json()["error"]["message"].lower()

    def test_sql_injection_with_delete_keyword(self, client):
        """Test SQL injection with DELETE keyword."""
        response = client.post(
            "/auth/register",
            params={"username": "DELETE_admin", "password": "test12345"},
        )
        assert response.status_code == 422

    def test_sql_injection_with_update_keyword(self, client):
        """Test SQL injection with UPDATE keyword."""
        response = client.post(
            "/auth/register",
            params={"username": "UPDATE_users", "password": "test12345"},
        )
        assert response.status_code == 422

    def test_sql_injection_with_select_keyword(self, client):
        """Test SQL injection with SELECT keyword."""
        response = client.post(
            "/auth/register",
            params={"username": "SELECT_star", "password": "test12345"},
        )
        assert response.status_code == 422

    def test_sql_injection_in_login_username(self, client):
        """Test SQL injection in login endpoint."""
        # Try SQL injection in login (should not crash)
        response = client.post(
            "/auth/login",
            params={"username": "admin' OR '1'='1", "password": "anything"},
        )
        # Should return invalid credentials, not crash
        assert response.status_code == 401
        assert "invalid_credentials" in response.json()["error"]["code"]

    def test_sql_injection_in_suggestions_status(self, client, auth_headers):
        """Test SQL injection in suggestions status filter."""
        headers = auth_headers()

        # Try SQL injection in status query parameter
        response = client.get(
            "/suggestions", params={"status": "new' OR '1'='1"}, headers=headers
        )
        # Should handle gracefully (SQLAlchemy parameterization protects)
        # Empty result is OK (no match for that status)
        assert response.status_code in [200, 422]

    def test_valid_username_with_underscore(self, client):
        """Test that valid usernames with underscore work."""
        response = client.post(
            "/auth/register",
            params={"username": "valid_user_123", "password": "test12345"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "valid_user_123"

    def test_valid_alphanumeric_username(self, client):
        """Test that valid alphanumeric usernames work."""
        response = client.post(
            "/auth/register", params={"username": "user123", "password": "test12345"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "user123"

    def test_sql_injection_with_backslash(self, client):
        """Test SQL injection with backslash escape."""
        response = client.post(
            "/auth/register", params={"username": "admin\\", "password": "test12345"}
        )
        assert response.status_code == 422

    def test_sql_injection_with_double_quote(self, client):
        """Test SQL injection with double quote."""
        response = client.post(
            "/auth/register", params={"username": 'admin"test', "password": "test12345"}
        )
        assert response.status_code == 422

    def test_sql_injection_with_comment_block(self, client):
        """Test SQL injection with comment block."""
        response = client.post(
            "/auth/register",
            params={"username": "admin/*comment*/", "password": "test12345"},
        )
        assert response.status_code == 422

    def test_parameterized_query_in_suggestions_create(self, client, auth_headers):
        """Test that suggestions are created with parameterized queries."""
        headers = auth_headers()

        # Try creating suggestion with SQL-like content (should be stored as-is)
        response = client.post(
            "/suggestions",
            headers=headers,
            json={
                "title": "Test' OR '1'='1",
                "text": "SELECT * FROM users; DROP TABLE users;",
                "status": "new",
            },
        )
        assert response.status_code == 200
        # Content should be stored as-is (parameterized query protects)
        assert "Test" in response.json()["title"]
        assert "SELECT" in response.json()["text"]

        # Verify it was stored correctly
        response = client.get(f"/suggestions/{response.json()['id']}", headers=headers)
        assert response.status_code == 200
