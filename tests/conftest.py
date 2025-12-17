import os
from unittest.mock import MagicMock, patch

import pytest

# Set dummy environment variables to prevent initialization errors
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "test-secret")
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "test-public")


# Mock the agent at module level before any imports
@pytest.fixture(scope="session", autouse=True)
def mock_agent_initialization():
    """Mock agent initialization to prevent API key requirements during tests."""
    with patch("src.agent.agent_runner.ChatGroq") as mock_groq:
        mock_groq.return_value = MagicMock()
        yield


@pytest.fixture(scope="session")
def app():
    """Provide the FastAPI app for testing."""
    from src.api.main import app

    return app


@pytest.fixture
def client(app):
    """Provide a test client for the FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(app)
