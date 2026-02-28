"""Tests for analytics endpoint authorization."""

import pytest
from unittest.mock import patch


class TestAnalyticsAuthorization:
    """Verify that analytics endpoints enforce business ownership."""

    # Endpoints that take business_id as a path parameter
    PATH_ENDPOINTS = [
        "/api/analytics/business/{bid}",
        "/api/analytics/business/{bid}/realtime",
    ]

    def test_own_business_returns_200(self, client):
        """Owner accessing their own business analytics should succeed."""
        # mock_user already has businesses=[MagicMock(id=1)] from conftest
        with patch("app.api.v1.endpoints.analytics.reporting_service") as mock_rs:
            mock_rs.generate_report.return_value = {"status": "ok"}
            mock_rs.get_realtime_stats.return_value = {"status": "ok"}

            for endpoint in self.PATH_ENDPOINTS:
                url = endpoint.format(bid=1)
                resp = client.get(url)
                assert resp.status_code == 200, f"{url} returned {resp.status_code}"

    def test_other_users_business_returns_403(self, client):
        """Accessing another user's business analytics should return 403."""
        for endpoint in self.PATH_ENDPOINTS:
            url = endpoint.format(bid=999)  # mock_user owns business id=1, not 999
            resp = client.get(url)
            assert resp.status_code == 403, f"{url} returned {resp.status_code}"
            assert resp.json()["detail"] == "Not enough permissions"

    def test_admin_bypasses_ownership_check(self, admin_client):
        """Admin users should access any business analytics."""
        with patch("app.api.v1.endpoints.analytics.reporting_service") as mock_rs:
            mock_rs.generate_report.return_value = {"status": "ok"}
            mock_rs.get_realtime_stats.return_value = {"status": "ok"}

            for endpoint in self.PATH_ENDPOINTS:
                url = endpoint.format(bid=999)
                resp = admin_client.get(url)
                assert resp.status_code == 200, f"{url} returned {resp.status_code}"

    def test_roi_endpoint_enforces_ownership(self, client):
        """ROI endpoint should reject non-owned business_id."""
        resp = client.get("/api/analytics/roi?business_id=999")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Not enough permissions"

    def test_roi_endpoint_allows_own_business(self, client):
        """ROI endpoint should allow owned business_id."""
        with patch("app.api.v1.endpoints.analytics.reporting_service") as mock_rs:
            mock_rs.calculate_roi_metrics.return_value = {"roi": 1.5}
            resp = client.get("/api/analytics/roi?business_id=1")
            assert resp.status_code == 200
