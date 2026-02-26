from datetime import timedelta, datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.models.models import User, RefreshToken
from app.schemas.user import Token, UserCreate, User as UserSchema, UserLogin, RefreshRequest

router = APIRouter()

@router.post("/signup", response_model=UserSchema)
@limiter.limit("3/minute")
def create_user(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        name=user_in.name,
        password=hashed_password,
        role=user_in.role,
        status="active"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login_access_token(
    request: Request,
    user_login: UserLogin,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        user = db.query(User).filter(User.email == user_login.email).first()
        if not user or not security.verify_password(user_login.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        elif user.status != "active":
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )

        # Create refresh token
        raw_refresh, token_hash = security.create_refresh_token()
        db_refresh = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(db_refresh)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        # Log unexpected errors for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during login. Please try again later."
        )

@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh_access_token(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    token_hash = security.hash_token(body.refresh_token)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    ).first()

    if not db_token or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old token (rotation)
    db_token.revoked = True

    # Issue new pair
    access_token = security.create_access_token(
        db_token.user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    raw_refresh, new_hash = security.create_refresh_token()
    new_db_token = RefreshToken(
        user_id=db_token.user_id,
        token_hash=new_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
    }

@router.post("/logout")
def logout(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Revoke all refresh tokens for the current user."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return {"detail": "Logged out successfully"}

@router.post("/approve-user/{user_id}", response_model=UserSchema)
async def approve_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Admin-only: approve a pending user"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = "active"
    db.commit()
    db.refresh(user)
    return user

@router.get("/pending-users")
async def list_pending_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Admin-only: list users awaiting approval"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    pending = db.query(User).filter(User.status == "pending").all()
    return [{"id": u.id, "email": u.email, "name": u.name, "created_at": u.created_at} for u in pending]
