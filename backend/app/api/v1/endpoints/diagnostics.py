"""
Diagnostic endpoint to help troubleshoot deployment issues (admin-only).
"""
import os
import sys
from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.models.models import User

router = APIRouter()

@router.get("/diagnostics")
def get_diagnostics(
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Returns diagnostic information to help troubleshoot deployment issues.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    diagnostics = {
        "python_version": sys.version,
        "environment": {},
        "database": {},
        "aws": {},
        "issues": []
    }

    # Check environment variables — only report SET / NOT_SET
    required_env_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "API_V1_STR"
    ]

    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            diagnostics["environment"][var] = "SET"
        else:
            diagnostics["environment"][var] = "NOT_SET"
            diagnostics["issues"].append(f"Missing required environment variable: {var}")

    # Check database configuration
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            diagnostics["database"]["status"] = "CONNECTED"
            diagnostics["database"]["engine"] = "ok"
    except Exception:
        diagnostics["database"]["status"] = "FAILED"
        diagnostics["database"]["error"] = "connection_failed"
        diagnostics["issues"].append("Database connection failed")

    # Check AWS configuration
    diagnostics["aws"]["access_key"] = "SET" if os.environ.get("AWS_ACCESS_KEY_ID") else "NOT_SET"
    diagnostics["aws"]["secret_key"] = "SET" if os.environ.get("AWS_SECRET_ACCESS_KEY") else "NOT_SET"
    diagnostics["aws"]["region"] = "SET" if os.environ.get("AWS_REGION") else "NOT_SET"

    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        diagnostics["issues"].append("AWS credentials not configured - AI features will not work")

    # Overall status
    if not diagnostics["issues"]:
        diagnostics["status"] = "HEALTHY"
    else:
        diagnostics["status"] = "ISSUES_FOUND"

    return diagnostics
