"""
Shared test fixtures for endpoint tests.

Provides mock database session, mock users, mock business, and
pre-configured TestClient instances with dependency overrides.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user, get_current_active_user
from app.models.models import User, Business


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    db.delete = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def mock_user():
    """Mock authenticated user with a business."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    user.role = "business_owner"
    user.status = "active"
    user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    business = MagicMock(spec=Business)
    business.id = 1
    business.user_id = user.id
    business.name = "Test Business"
    user.businesses = [business]

    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    user = MagicMock(spec=User)
    user.id = 99
    user.email = "admin@example.com"
    user.name = "Admin User"
    user.role = "admin"
    user.status = "active"
    user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user.businesses = []
    return user


@pytest.fixture
def mock_business():
    """Mock business object."""
    business = MagicMock(spec=Business)
    business.id = 1
    business.user_id = 1
    business.name = "Test Business"
    business.type = "restaurant"
    return business


@pytest.fixture
def client(mock_db, mock_user):
    """Authenticated TestClient with DB and user overrides."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(mock_db):
    """TestClient with only DB override (for login/signup/refresh tests)."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(mock_db, mock_admin_user):
    """Authenticated TestClient with admin user."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
