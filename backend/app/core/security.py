from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Tuple
import hashlib
import secrets
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_refresh_token() -> Tuple[str, str]:
    """Generate a refresh token. Returns (raw_token, sha256_hash)."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
