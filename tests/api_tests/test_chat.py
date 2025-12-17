import uuid
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage


class TestChatEndpoint:
    """Tests for the /chat endpoint."""

    @patch("src.api.routes.chat.agent")
    def test_chat_success_with_thread_id(self, mock_agent, client):
        """Test successful chat with provided thread_id."""

        mock_agent.invoke.return_value = {
            "messages": [HumanMessage(content="Hello"), AIMessage(content="Hi there!")]
        }

        request_data = {
            "message": "Hello",
            "thread_id": "test-thread-123",
        }

        response = client.post("/chat/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hi there!"
        assert data["thread_id"] == request_data["thread_id"]

        # Verify agent was called with correct config
        call_args = mock_agent.invoke.call_args
        assert call_args.args[0]["messages"][0].content == "Hello"
        assert (
            call_args.kwargs["config"]["configurable"]["thread_id"]
            == request_data["thread_id"]
        )

    @patch("src.api.routes.chat.agent")
    @patch("uuid.uuid4")
    def test_chat_success_without_thread_id(self, mock_uuid, mock_agent, client):
        """Test successful chat without thread_id (should generate new one)."""
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_agent.invoke.return_value = {
            "messages": [HumanMessage(content="Hello"), AIMessage(content="Hi there!")]
        }

        request_data = {"message": "Hello"}

        response = client.post("/chat/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hi there!"
        assert data["thread_id"] == "12345678-1234-5678-1234-567812345678"

    @patch("src.api.routes.chat.agent")
    def test_chat_handles_agent_exception(self, mock_agent, client):
        """Test chat endpoint handles agent exceptions gracefully."""
        mock_agent.invoke.side_effect = Exception("Agent error")

        request_data = {"message": "Hello", "thread_id": "test-thread"}

        with pytest.raises(Exception):
            client.post("/chat/", json=request_data)

    def test_chat_missing_message(self, client):
        """Test chat with missing message field."""
        response = client.post("/chat/", json={})
        assert response.status_code == 422  # Validation error
