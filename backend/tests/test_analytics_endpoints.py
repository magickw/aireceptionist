"""Tests for analytics endpoint authorization."""

import pytest
from unittest.mock import MagicMock, patch
from app.models.models import Business


class TestAnalyticsAuthorization:
    """Verify that analytics endpoints enforce business ownership."""

    ENDPOINTS = [
        "/api/analytics/business/{bid}",
        "/api/analytics/business/{bid}/revenue",
        "/api/analytics/business/{bid}/realtime",
        "/api/analytics/business/{bid}/active-calls",
    ]

    def test_own_business_returns_200(self, client, mock_db, mock_user):
        """Owner accessing their own business analytics should succeed."""
        own_business = MagicMock(spec=Business)
        own_business.id = 1
        own_business.user_id = mock_user.id

        mock_db.query.return_value.filter.return_value.first.return_value = own_business
        # For chained query calls (count, all, group_by, etc.) return sensible defaults
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        for endpoint in self.ENDPOINTS:
            url = endpoint.format(bid=1)
            resp = client.get(url)
            assert resp.status_code == 200, f"{url} returned {resp.status_code}"

    def test_other_users_business_returns_400(self, client, mock_db, mock_user):
        """Accessing another user's business analytics should return 400."""
        other_business = MagicMock(spec=Business)
        other_business.id = 999
        other_business.user_id = 42  # Different from mock_user.id (1)

        mock_db.query.return_value.filter.return_value.first.return_value = other_business

        for endpoint in self.ENDPOINTS:
            url = endpoint.format(bid=999)
            resp = client.get(url)
            assert resp.status_code == 400, f"{url} returned {resp.status_code}"
            assert resp.json()["detail"] == "Not enough permissions"

    def test_nonexistent_business_returns_400(self, client, mock_db):
        """Accessing analytics for a non-existent business should return 400."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        for endpoint in self.ENDPOINTS:
            url = endpoint.format(bid=99999)
            resp = client.get(url)
            assert resp.status_code == 400, f"{url} returned {resp.status_code}"
            assert resp.json()["detail"] == "Not enough permissions"

    def test_admin_bypasses_ownership_check(self, admin_client, mock_db):
        """Admin users should access any business analytics."""
        # Admin skips the ownership query entirely, so set up data queries
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        for endpoint in self.ENDPOINTS:
            url = endpoint.format(bid=999)
            resp = admin_client.get(url)
            assert resp.status_code == 200, f"{url} returned {resp.status_code}"
