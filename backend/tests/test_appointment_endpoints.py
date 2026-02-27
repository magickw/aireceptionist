"""Tests for appointment endpoints: list, create, update, permission checks."""

import pytest
from unittest.mock import MagicMock, PropertyMock
from datetime import datetime, timezone

from app.models.models import Appointment, Business


class TestListAppointments:
    def test_list_by_business(self, client, mock_db, mock_user):
        business = MagicMock(spec=Business)
        business.id = 1
        business.user_id = mock_user.id

        appt = MagicMock(spec=Appointment)
        appt.id = 1
        appt.business_id = 1
        appt.customer_name = "Alice"
        appt.customer_phone = "555-0001"
        appt.appointment_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
        appt.service_type = "Consultation"
        appt.status = "scheduled"
        appt.source = "internal"
        appt.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        appt.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        appt.customer_id = None
        appt.no_show_probability = None
        appt.reminder_sent = False
        appt.notes = None

        # First query().filter() call is for business ownership check
        # Second query().filter() call is for appointments list
        mock_db.query.return_value.filter.return_value.first.return_value = business
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [appt]

        response = client.get("/api/appointments/business/1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["customer_name"] == "Alice"

    def test_list_permission_denied(self, client, mock_db, mock_user):
        # Business owned by someone else
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/api/appointments/business/999")
        assert response.status_code == 400
        assert "permissions" in response.json()["detail"].lower()


class TestCreateAppointment:
    def test_create_success(self, client, mock_db, mock_user):
        business = MagicMock(spec=Business)
        business.id = 1
        business.user_id = mock_user.id
        mock_db.query.return_value.filter.return_value.first.return_value = business

        appt_data = {
            "business_id": 1,
            "customer_name": "Bob",
            "customer_phone": "555-0002",
            "appointment_time": "2026-03-01T14:00:00Z",
            "service_type": "Haircut",
        }

        def fake_refresh(obj):
            obj.id = 10
            obj.business_id = 1
            obj.customer_name = "Bob"
            obj.customer_phone = "555-0002"
            obj.appointment_time = datetime(2026, 3, 1, 14, 0, tzinfo=timezone.utc)
            obj.service_type = "Haircut"
            obj.status = "scheduled"
            obj.source = "internal"
            obj.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
            obj.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        mock_db.refresh = fake_refresh

        response = client.post("/api/appointments/", json=appt_data)
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == "Bob"
        assert data["service_type"] == "Haircut"
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    def test_create_permission_denied(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post("/api/appointments/", json={
            "business_id": 999,
            "customer_name": "Charlie",
            "customer_phone": "555-0003",
            "appointment_time": "2026-03-01T14:00:00Z",
        })
        assert response.status_code == 400


class TestUpdateAppointment:
    def test_update_success(self, client, mock_db, mock_user):
        appt = MagicMock(spec=Appointment)
        appt.id = 1
        appt.business_id = 1

        business = MagicMock(spec=Business)
        business.id = 1
        business.user_id = mock_user.id

        # First call returns appointment, second returns business
        mock_db.query.return_value.filter.return_value.first.side_effect = [appt, business]

        def fake_refresh(obj):
            obj.id = 1
            obj.business_id = 1
            obj.customer_name = "Updated"
            obj.customer_phone = "555-9999"
            obj.appointment_time = datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc)
            obj.service_type = "Follow-up"
            obj.status = "scheduled"
            obj.source = "internal"
            obj.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
            obj.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        mock_db.refresh = fake_refresh

        response = client.put("/api/appointments/1", json={
            "customer_name": "Updated",
            "customer_phone": "555-9999",
            "appointment_time": "2026-03-02T10:00:00Z",
        })
        assert response.status_code == 200
        assert response.json()["customer_name"] == "Updated"

    def test_update_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.put("/api/appointments/999", json={
            "customer_name": "Ghost",
            "customer_phone": "555-0000",
            "appointment_time": "2026-03-02T10:00:00Z",
        })
        assert response.status_code == 404
