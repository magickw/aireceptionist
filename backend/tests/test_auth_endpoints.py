"""Tests for auth endpoints: signup, login, refresh, logout, me."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.models.models import User, RefreshToken


class TestSignup:
    def test_signup_success(self, unauthenticated_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        new_user = MagicMock(spec=User)
        new_user.id = 2
        new_user.email = "new@example.com"
        new_user.name = "New User"
        new_user.role = "business_owner"
        new_user.status = "active"
        new_user.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        def fake_refresh(obj):
            obj.id = new_user.id
            obj.email = new_user.email
            obj.name = new_user.name
            obj.role = new_user.role
            obj.status = new_user.status
            obj.created_at = new_user.created_at

        mock_db.refresh = fake_refresh

        response = unauthenticated_client.post("/api/auth/signup", json={
            "email": "new@example.com",
            "name": "New User",
            "password": "Secret123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["name"] == "New User"

    def test_signup_duplicate_email(self, unauthenticated_client, mock_db):
        existing = MagicMock(spec=User)
        existing.email = "existing@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        response = unauthenticated_client.post("/api/auth/signup", json={
            "email": "existing@example.com",
            "name": "Dup User",
            "password": "Secret123",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestLogin:
    @patch("app.api.v1.endpoints.auth.security")
    def test_login_success(self, mock_security, unauthenticated_client, mock_db):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.password = "hashed"
        user.status = "active"
        user.locked_until = None
        user.failed_login_attempts = 0
        mock_db.query.return_value.filter.return_value.first.return_value = user

        mock_security.verify_password.return_value = True
        mock_security.create_access_token.return_value = "fake-access-token"
        mock_security.create_refresh_token.return_value = ("fake-refresh", "fake-hash")

        response = unauthenticated_client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "correct",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "fake-access-token"
        assert data["refresh_token"] == "fake-refresh"
        assert data["token_type"] == "bearer"

    @patch("app.api.v1.endpoints.auth.security")
    def test_login_wrong_password(self, mock_security, unauthenticated_client, mock_db):
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.password = "hashed"
        user.status = "active"
        user.locked_until = None
        user.failed_login_attempts = 0
        mock_db.query.return_value.filter.return_value.first.return_value = user

        mock_security.verify_password.return_value = False

        response = unauthenticated_client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrong",
        })
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    @patch("app.api.v1.endpoints.auth.security")
    def test_login_nonexistent_user(self, mock_security, unauthenticated_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = unauthenticated_client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "anything",
        })
        assert response.status_code == 401


class TestRefresh:
    @patch("app.api.v1.endpoints.auth.security")
    def test_refresh_success(self, mock_security, unauthenticated_client, mock_db):
        token_record = MagicMock(spec=RefreshToken)
        token_record.user_id = 1
        token_record.revoked = False
        token_record.expires_at = datetime.now(timezone.utc) + timedelta(days=1)

        mock_security.hash_token.return_value = "hashed-token"
        mock_db.query.return_value.filter.return_value.first.return_value = token_record
        mock_security.create_access_token.return_value = "new-access"
        mock_security.create_refresh_token.return_value = ("new-refresh", "new-hash")

        response = unauthenticated_client.post("/api/auth/refresh", json={
            "refresh_token": "old-refresh-token",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access"
        assert data["refresh_token"] == "new-refresh"
        assert token_record.revoked is True

    @patch("app.api.v1.endpoints.auth.security")
    def test_refresh_invalid_token(self, mock_security, unauthenticated_client, mock_db):
        mock_security.hash_token.return_value = "bad-hash"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = unauthenticated_client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert response.status_code == 401

    @patch("app.api.v1.endpoints.auth.security")
    def test_refresh_expired_token(self, mock_security, unauthenticated_client, mock_db):
        token_record = MagicMock(spec=RefreshToken)
        token_record.user_id = 1
        token_record.revoked = False
        token_record.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        mock_security.hash_token.return_value = "hashed"
        mock_db.query.return_value.filter.return_value.first.return_value = token_record

        response = unauthenticated_client.post("/api/auth/refresh", json={
            "refresh_token": "expired-token",
        })
        assert response.status_code == 401


class TestLogout:
    def test_logout_revokes_tokens(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.update.return_value = 2

        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["detail"] == "Logged out successfully"
        mock_db.commit.assert_called()


class TestMe:
    def test_me_returns_user(self, client, mock_user):
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name
