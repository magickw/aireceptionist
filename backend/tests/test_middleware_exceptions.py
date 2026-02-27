"""Tests for request logging middleware and global exception handlers."""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError

from app.models.models import Business


class TestRequestLoggingMiddleware:
    """Verify RequestLoggingMiddleware sets X-Request-Id."""

    def test_x_request_id_header_present(self, client):
        resp = client.get("/api/auth/me")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) == 8


class TestExceptionHandlers:
    """Verify global exception handlers return safe JSON."""

    def test_integrity_error_returns_409(self, client, mock_db, mock_user):
        """IntegrityError should return 409 with no SQL in body."""
        # Make the ownership check pass for the appointments endpoint
        own_business = MagicMock(spec=Business)
        own_business.id = 1
        own_business.user_id = mock_user.id
        mock_db.query.return_value.filter.return_value.first.return_value = own_business
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        # Then make commit raise IntegrityError
        mock_db.commit.side_effect = IntegrityError(
            "INSERT INTO appointments ...", {}, Exception("duplicate key")
        )

        resp = client.post(
            "/api/appointments",
            json={
                "business_id": 1,
                "customer_name": "Test",
                "customer_phone": "1234567890",
                "appointment_time": "2026-03-01T10:00:00",
            },
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "detail" in body
        # Must NOT leak SQL
        assert "INSERT" not in body["detail"]
        assert "duplicate key" not in body["detail"]

    def test_generic_exception_returns_500_no_stacktrace(self, mock_db, mock_admin_user):
        """Unhandled exceptions should return 500 with no stack trace."""
        from app.main import app
        from app.api.deps import get_db, get_current_user, get_current_active_user
        from fastapi.testclient import TestClient

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_admin_user
        app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user

        # Admin bypasses ownership check; db.query directly raises
        mock_db.query.side_effect = RuntimeError("unexpected DB crash")

        try:
            with TestClient(app, raise_server_exceptions=False) as c:
                resp = c.get("/api/analytics/business/1")
                assert resp.status_code == 500
                body = resp.json()
                assert "detail" in body
                assert "unexpected DB crash" not in body["detail"]
                assert "Traceback" not in body.get("detail", "")
        finally:
            app.dependency_overrides.clear()
