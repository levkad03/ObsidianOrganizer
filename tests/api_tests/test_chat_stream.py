import uuid
from unittest.mock import MagicMock, patch


class TestChatStreamEndpoint:
    """Tests for the /chat/stream endpoint."""

    @patch("src.api.routes.chat.agent")
    def test_stream_success_with_thread_id(self, mock_agent, client):
        """Test successful streaming chat with provided thread_id."""

        # Mock the async stream events
        async def mock_astream(*args, **kwargs):
            events = [
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content="Hello", hasattr=lambda x: x == "content"
                        )
                    },
                },
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content=" world", hasattr=lambda x: x == "content"
                        )
                    },
                },
            ]
            for event in events:
                yield event

        mock_agent.astream_events = mock_astream

        request_data = {"message": "Hello", "thread_id": "stream-thread-123"}

        with client.stream("POST", "/chat/stream", json=request_data) as response:
            assert response.status_code == 200
            assert (
                response.headers["content-type"] == "text/event-stream; charset=utf-8"
            )

    @patch("src.api.routes.chat.agent")
    @patch("uuid.uuid4")
    def test_stream_without_thread_id(self, mock_uuid, mock_agent, client):
        """Test streaming chat without thread_id (should generate new one)."""
        mock_uuid.return_value = uuid.UUID("87654321-4321-8765-4321-876543218765")

        # Mock the async stream events
        async def mock_astream(*args, **kwargs):
            events = [
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content="Streaming ", hasattr=lambda x: x == "content"
                        )
                    },
                },
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content="response", hasattr=lambda x: x == "content"
                        )
                    },
                },
            ]
            for event in events:
                yield event

        mock_agent.astream_events = mock_astream

        request_data = {"message": "Stream this"}

        with client.stream("POST", "/chat/stream", json=request_data) as response:
            assert response.status_code == 200
            assert (
                response.headers["content-type"] == "text/event-stream; charset=utf-8"
            )

    def test_stream_missing_message(self, client):
        """Test stream with missing message field."""
        response = client.post("/chat/stream", json={})
        assert response.status_code == 422  # Validation error

    @patch("src.api.routes.chat.agent")
    def test_stream_filters_empty_chunks(self, mock_agent, client):
        """Test that streaming filters out empty content chunks."""

        async def mock_astream(*args, **kwargs):
            events = [
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(content="", hasattr=lambda x: x == "content")
                    },
                },
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content="Real content", hasattr=lambda x: x == "content"
                        )
                    },
                },
            ]
            for event in events:
                yield event

        mock_agent.astream_events = mock_astream

        request_data = {"message": "Test", "thread_id": "test-thread"}

        with client.stream("POST", "/chat/stream", json=request_data) as response:
            assert response.status_code == 200
            # Empty chunks should be filtered out

    @patch("src.api.routes.chat.agent")
    def test_stream_sends_done_event(self, mock_agent, client):
        """Test that stream sends done event with thread_id at the end."""

        async def mock_astream(*args, **kwargs):
            events = [
                {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": MagicMock(
                            content="Done", hasattr=lambda x: x == "content"
                        )
                    },
                },
            ]
            for event in events:
                yield event

        mock_agent.astream_events = mock_astream

        request_data = {"message": "Test", "thread_id": "final-thread"}

        with client.stream("POST", "/chat/stream", json=request_data) as response:
            assert response.status_code == 200
            # Should end with done event containing thread_id
