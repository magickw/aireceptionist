"""Tests for security headers middleware."""

import pytest


EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "x-xss-protection": "1; mode=block",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}


class TestSecurityHeaders:
    """Verify that all responses include required security headers."""

    def test_health_endpoint_has_security_headers(self, client):
        resp = client.get("/health")
        for header, expected_value in EXPECTED_HEADERS.items():
            actual = resp.headers.get(header)
            assert actual == expected_value, (
                f"Header '{header}' expected '{expected_value}', got '{actual}'"
            )

    def test_api_endpoint_has_security_headers(self, client):
        resp = client.get("/api/auth/me")
        for header, expected_value in EXPECTED_HEADERS.items():
            actual = resp.headers.get(header)
            assert actual == expected_value, (
                f"Header '{header}' expected '{expected_value}', got '{actual}'"
            )
