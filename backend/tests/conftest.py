import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from routers.auth import create_access_token


@pytest.fixture(scope="session", autouse=True)
def mock_db_pool():
    """Mock database pool on FastAPI app state."""
    mock_pool = MagicMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.fetch = AsyncMock(return_value=[])
    mock_pool.execute = AsyncMock(return_value=None)
    app.state.pool = mock_pool
    yield mock_pool


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_a_token():
    """Valid JWT token for User A."""
    return create_access_token("user_a_id_12345", 0)


@pytest.fixture
def user_b_token():
    """Valid JWT token for User B."""
    return create_access_token("user_b_id_67890", 0)


@pytest.fixture
def auth_headers_user_a(user_a_token):
    return {"Authorization": f"Bearer {user_a_token}"}


@pytest.fixture
def auth_headers_user_b(user_b_token):
    return {"Authorization": f"Bearer {user_b_token}"}

