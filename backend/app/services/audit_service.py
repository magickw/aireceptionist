"""Audit log utility for recording user actions."""

import logging
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    *,
    user_id: Optional[int] = None,
    business_id: Optional[int] = None,
    operation: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    old_values: Optional[Any] = None,
    new_values: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Add an audit log entry to the session.

    The entry is committed with the caller's transaction.
    Exceptions are caught and logged so that audit failures
    never break the primary operation.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            business_id=business_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
    except Exception:
        logger.exception("Failed to create audit log for operation=%s", operation)
