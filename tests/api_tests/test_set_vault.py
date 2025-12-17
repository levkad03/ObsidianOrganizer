from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestSetVaultEndpoint:
    """Tests for the /chat/set-vault endpoint."""

    @patch("src.api.routes.chat.set_vault")
    def test_set_vault_success(self, mock_set_vault):
        """Test successful vault path configuration."""

        request_data = {
            "thread_id": "test-thread-123",
            "vault_path": "path/to/vault",
        }

        response = client.post("/chat/set-vault", json=request_data)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["thread_id"] == request_data["thread_id"]
        assert "successfully" in response.json()["message"].lower()
        mock_set_vault.assert_called_once_with(
            request_data["thread_id"], request_data["vault_path"]
        )

    @patch("src.api.routes.chat.set_vault")
    def test_set_vault_invalid_path(self, mock_set_vault):
        """Test vault configuration with invalid path."""

        mock_set_vault.side_effect = ValueError("Invalid vault path")

        request_data = {
            "thread_id": "test-thread-123",
            "vault_path": "invalid/path",
        }

        response = client.post("/chat/set-vault", json=request_data)

        assert response.status_code == 400
        assert "Invalid vault path" in response.json()["detail"]

    def test_set_vault_missing_fields(self):
        """Test vault configuration with missing fields."""

        request_data = {
            "thread_id": "test-thread-123",
            # Missing 'vault_path'
        }

        response = client.post("/chat/set-vault", json=request_data)

        assert response.status_code == 422  # Unprocessable Entity
