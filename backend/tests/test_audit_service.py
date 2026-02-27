"""Tests for the audit service."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.audit_service import create_audit_log
from app.models.models import AuditLog


class TestCreateAuditLog:
    def test_adds_entry_to_session(self):
        db = MagicMock()
        create_audit_log(
            db,
            user_id=1,
            business_id=2,
            operation="order.create",
            resource_type="order",
            resource_id=42,
            new_values={"status": "pending"},
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
        )
        db.add.assert_called_once()
        entry = db.add.call_args[0][0]
        assert isinstance(entry, AuditLog)
        assert entry.operation == "order.create"
        assert entry.user_id == 1
        assert entry.business_id == 2
        assert entry.resource_id == "42"
        assert entry.ip_address == "127.0.0.1"

    def test_handles_exception_silently(self):
        db = MagicMock()
        db.add.side_effect = RuntimeError("DB error")
        # Should not raise
        create_audit_log(
            db,
            operation="order.create",
        )

    def test_optional_fields_default_to_none(self):
        db = MagicMock()
        create_audit_log(db, operation="test.op")
        entry = db.add.call_args[0][0]
        assert entry.user_id is None
        assert entry.business_id is None
        assert entry.resource_type is None
        assert entry.old_values is None
        assert entry.new_values is None
