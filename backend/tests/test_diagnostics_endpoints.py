"""Tests for diagnostics endpoint authorization and info redaction."""

import pytest


class TestDiagnosticsEndpoint:
    """Verify diagnostics requires admin auth and redacts sensitive info."""

    def test_unauthenticated_returns_401(self, unauthenticated_client):
        """Unauthenticated request should be rejected."""
        resp = unauthenticated_client.get("/api/diagnostics")
        assert resp.status_code in (401, 403)

    def test_non_admin_returns_403(self, client):
        """Non-admin authenticated user should be rejected."""
        resp = client.get("/api/diagnostics")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Admin access required"

    def test_admin_returns_200(self, admin_client):
        """Admin user should get diagnostics."""
        resp = admin_client.get("/api/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert "environment" in data
        assert "database" in data

    def test_env_vars_are_redacted(self, admin_client):
        """Environment variables should only show SET or NOT_SET."""
        resp = admin_client.get("/api/diagnostics")
        data = resp.json()
        for var, value in data["environment"].items():
            assert value in ("SET", "NOT_SET"), f"{var} leaked value: {value}"

    def test_aws_region_is_redacted(self, admin_client):
        """AWS region should not leak the actual region name."""
        resp = admin_client.get("/api/diagnostics")
        data = resp.json()
        assert data["aws"]["region"] in ("SET", "NOT_SET")

    def test_db_error_is_generic(self, admin_client):
        """Database errors should not leak connection strings."""
        resp = admin_client.get("/api/diagnostics")
        data = resp.json()
        if data["database"].get("error"):
            assert data["database"]["error"] == "connection_failed"
