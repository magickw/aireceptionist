"""
Diagnostic endpoint to help troubleshoot Vercel deployment issues
"""
import os
import sys
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/diagnostics")
def get_diagnostics():
    """
    Returns diagnostic information to help troubleshoot deployment issues
    """
    diagnostics = {
        "python_version": sys.version,
        "environment": {},
        "database": {},
        "aws": {},
        "issues": []
    }
    
    # Check environment variables (safe display)
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
            # Show partial value for security
            if var == "DATABASE_URL":
                # Show host only, hide password
                parts = value.split("@")
                if len(parts) > 1:
                    diagnostics["environment"][var] = f"***@{parts[1]}"
                else:
                    diagnostics["environment"][var] = "SET"
            elif var in ["SECRET_KEY", "AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID"]:
                diagnostics["environment"][var] = "SET"
            else:
                diagnostics["environment"][var] = value
        else:
            diagnostics["environment"][var] = "NOT_SET"
            diagnostics["issues"].append(f"Missing required environment variable: {var}")
    
    # Check database configuration
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            diagnostics["database"]["status"] = "CONNECTED"
            diagnostics["database"]["engine"] = str(engine.url.driver)
    except Exception as e:
        diagnostics["database"]["status"] = "FAILED"
        diagnostics["database"]["error"] = str(e)
        diagnostics["issues"].append(f"Database connection failed: {str(e)}")
    
    # Check AWS configuration
    diagnostics["aws"]["access_key"] = "SET" if os.environ.get("AWS_ACCESS_KEY_ID") else "NOT_SET"
    diagnostics["aws"]["secret_key"] = "SET" if os.environ.get("AWS_SECRET_ACCESS_KEY") else "NOT_SET"
    diagnostics["aws"]["region"] = os.environ.get("AWS_REGION", "NOT_SET")
    
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        diagnostics["issues"].append("AWS credentials not configured - AI features will not work")
    
    # Check SECRET_KEY
    if not os.environ.get("SECRET_KEY"):
        diagnostics["issues"].append("SECRET_KEY not set - Authentication will fail")
    elif len(os.environ.get("SECRET_KEY", "")) < 32:
        diagnostics["issues"].append("SECRET_KEY is too short - should be at least 32 characters")
    
    # Overall status
    if not diagnostics["issues"]:
        diagnostics["status"] = "HEALTHY"
    else:
        diagnostics["status"] = "ISSUES_FOUND"
    
    return diagnostics