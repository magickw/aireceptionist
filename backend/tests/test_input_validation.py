"""Tests for input validation across schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate
from app.schemas.appointment import AppointmentCreate
from app.schemas.order import OrderItemBase, OrderBase
from app.schemas.business import BusinessBase


class TestPasswordPolicy:
    def test_short_password_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="a@b.com", name="Test", password="Sh0rt")
        assert "at least 8" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_no_uppercase_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="a@b.com", name="Test", password="alllower1")
        assert "uppercase" in str(exc_info.value).lower()

    def test_no_lowercase_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="a@b.com", name="Test", password="ALLUPPER1")
        assert "lowercase" in str(exc_info.value).lower()

    def test_no_digit_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="a@b.com", name="Test", password="NoDigitsHere")
        assert "digit" in str(exc_info.value).lower()

    def test_valid_password_accepted(self):
        user = UserCreate(email="a@b.com", name="Test", password="Valid1Pass")
        assert user.password == "Valid1Pass"


class TestNameValidation:
    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", name="", password="Valid1Pass")

    def test_valid_name_accepted(self):
        user = UserCreate(email="a@b.com", name="A", password="Valid1Pass")
        assert user.name == "A"


class TestPhoneValidation:
    def test_invalid_phone_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            AppointmentCreate(
                customer_name="Test",
                customer_phone="abc",
                appointment_time="2026-03-01T10:00:00",
                business_id=1,
            )
        assert "phone" in str(exc_info.value).lower()

    def test_valid_phone_accepted(self):
        appt = AppointmentCreate(
            customer_name="Test",
            customer_phone="+1234567890",
            appointment_time="2026-03-01T10:00:00",
            business_id=1,
        )
        assert appt.customer_phone == "+1234567890"

    def test_phone_with_dashes_accepted(self):
        appt = AppointmentCreate(
            customer_name="Test",
            customer_phone="+1-234-567-890",
            appointment_time="2026-03-01T10:00:00",
            business_id=1,
        )
        assert appt.customer_phone == "+1-234-567-890"


class TestOrderValidation:
    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            OrderItemBase(item_name="Burger", quantity=-1, unit_price=9.99)

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            OrderItemBase(item_name="Burger", quantity=0, unit_price=9.99)

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            OrderItemBase(item_name="Burger", quantity=1, unit_price=-5.0)

    def test_empty_item_name_rejected(self):
        with pytest.raises(ValidationError):
            OrderItemBase(item_name="", quantity=1, unit_price=9.99)

    def test_invalid_order_status_rejected(self):
        with pytest.raises(ValidationError):
            OrderBase(status="invalid_status")

    def test_valid_order_status_accepted(self):
        order = OrderBase(status="preparing")
        assert order.status == "preparing"


class TestBusinessValidation:
    def test_invalid_business_type_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            BusinessBase(name="My Biz", type="invalid_type_xyz")
        assert "business type" in str(exc_info.value).lower()

    def test_valid_business_type_accepted(self):
        biz = BusinessBase(name="My Biz", type="restaurant")
        assert biz.type == "restaurant"

    def test_general_type_accepted(self):
        biz = BusinessBase(name="My Biz", type="general")
        assert biz.type == "general"

    def test_empty_business_name_rejected(self):
        with pytest.raises(ValidationError):
            BusinessBase(name="")
