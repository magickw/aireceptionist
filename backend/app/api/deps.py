from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import User, Business
from app.schemas.user import TokenPayload

# Define reusable OAuth2 scheme
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # We'll handle the error manually to allow token from query
)

# 1. Define get_db() FIRST
def get_db() -> Generator:
    """
    Dependency to get a database session.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# 2. THEN define get_current_user(), which depends on get_db()
async def get_current_user(
    db: Session = Depends(get_db),
    token_header: Optional[str] = Depends(reusable_oauth2),
    token_query: Optional[str] = Query(None, alias="token")
) -> User:
    """
    Dependency to get the current user from a token.
    Token can be in the Authorization header or as a 'token' query parameter.
    Supports both JWT tokens and Firebase tokens.
    """
    token = token_header or token_query
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try JWT token first (local validation, no network call)
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user = db.query(User).filter(User.id == token_data.sub).first()
        if user:
            return user
    except (JWTError, ValidationError):
        pass

    # Fall back to Firebase token (requires network call to Google)
    try:
        import asyncio
        firebase_payload = await asyncio.to_thread(
            _verify_firebase_token_sync, token
        )
        user = db.query(User).filter(User.email == firebase_payload.get("email")).first()
        if not user:
            # Create user if doesn't exist
            user = User(
                email=firebase_payload.get("email"),
                name=firebase_payload.get("name") or firebase_payload.get("display_name", "") or firebase_payload.get("email", "").split("@")[0],
                password="",  # Firebase users don't have local password
                status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )


def _verify_firebase_token_sync(token: str) -> dict:
    """Synchronous Firebase token verification for use with asyncio.to_thread."""
    from app.core.firebase_auth import get_firebase_app
    from firebase_admin import auth as firebase_auth
    app = get_firebase_app()
    return firebase_auth.verify_id_token(token, app=app)

# 3. Other dependencies can now use get_current_user
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active user.
    """
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_business_id(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependency to get the business ID for the current user.
    """
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(
            status_code=404,
            detail="No business found for this user. Please complete business setup."
        )
    return business.id
