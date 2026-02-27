"""Tests for order endpoints: list, get, create, update, delete, 404 handling."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from app.models.models import Order, OrderItem, Business


class TestListOrders:
    def test_list_orders(self, client, mock_db, mock_user):
        order = MagicMock(spec=Order)
        order.id = 1
        order.business_id = 1
        order.customer_name = "Alice"
        order.customer_phone = "555-0001"
        order.status = "pending"
        order.total_amount = 25.98
        order.delivery_method = None
        order.delivery_address = None
        order.notes = None
        order.call_session_id = None
        order.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.items = []

        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [order]

        response = client.get("/api/orders/", params={"business_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["customer_name"] == "Alice"


class TestGetOrder:
    def test_get_order_by_id(self, client, mock_db, mock_user):
        order = MagicMock(spec=Order)
        order.id = 1
        order.business_id = 1
        order.customer_name = "Bob"
        order.customer_phone = "555-0002"
        order.status = "confirmed"
        order.total_amount = 15.99
        order.delivery_method = "pickup"
        order.delivery_address = None
        order.notes = "Extra napkins"
        order.call_session_id = None
        order.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.items = []

        mock_db.query.return_value.filter.return_value.first.return_value = order

        response = client.get("/api/orders/1")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == "Bob"
        assert data["status"] == "confirmed"

    def test_get_order_not_found(self, client, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/api/orders/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateOrder:
    @patch("app.api.v1.endpoints.orders.OrderItem")
    @patch("app.api.v1.endpoints.orders.Order")
    def test_create_with_items(self, MockOrder, MockOrderItem, client, mock_db, mock_user):
        # Create the mock order that the Order() constructor returns
        mock_order = MagicMock()
        mock_order.id = 10
        mock_order.business_id = 1
        mock_order.customer_name = "Charlie"
        mock_order.customer_phone = "555-0003"
        mock_order.status = "pending"
        mock_order.total_amount = 34.97
        mock_order.delivery_method = None
        mock_order.delivery_address = None
        mock_order.notes = "Ring the bell"
        mock_order.call_session_id = None
        mock_order.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        mock_order.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        item1 = MagicMock()
        item1.id = 1
        item1.order_id = 10
        item1.menu_item_id = 1
        item1.item_name = "Burger"
        item1.quantity = 2
        item1.unit_price = 12.99
        item1.notes = None
        item1.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        item2 = MagicMock()
        item2.id = 2
        item2.order_id = 10
        item2.menu_item_id = 2
        item2.item_name = "Salad"
        item2.quantity = 1
        item2.unit_price = 8.99
        item2.notes = "No croutons"
        item2.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)

        mock_order.items = [item1, item2]

        MockOrder.return_value = mock_order
        MockOrderItem.side_effect = lambda **kwargs: MagicMock(**kwargs)

        response = client.post("/api/orders/", json={
            "customer_name": "Charlie",
            "customer_phone": "555-0003",
            "notes": "Ring the bell",
            "items": [
                {"item_name": "Burger", "quantity": 2, "unit_price": 12.99, "menu_item_id": 1},
                {"item_name": "Salad", "quantity": 1, "unit_price": 8.99, "menu_item_id": 2, "notes": "No croutons"},
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "Charlie"
        assert len(data["items"]) == 2
        assert data["total_amount"] == pytest.approx(34.97, abs=0.01)


class TestUpdateOrder:
    def test_update_status(self, client, mock_db, mock_user):
        order = MagicMock(spec=Order)
        order.id = 1
        order.business_id = 1
        order.customer_name = "Dave"
        order.customer_phone = "555-0004"
        order.status = "pending"
        order.total_amount = 20.00
        order.delivery_method = None
        order.delivery_address = None
        order.notes = None
        order.call_session_id = None
        order.created_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.updated_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
        order.items = []

        mock_db.query.return_value.filter.return_value.first.return_value = order

        def fake_refresh(obj):
            obj.status = "confirmed"

        mock_db.refresh = fake_refresh

        response = client.put("/api/orders/1", json={"status": "confirmed"})
        assert response.status_code == 200


class TestDeleteOrder:
    def test_delete_success(self, client, mock_db, mock_user):
        order = MagicMock(spec=Order)
        order.id = 1
        order.business_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = order

        response = client.delete("/api/orders/1")
        assert response.status_code == 200
        mock_db.delete.assert_called_once_with(order)
        mock_db.commit.assert_called()

    def test_delete_not_found(self, client, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete("/api/orders/999")
        assert response.status_code == 404
