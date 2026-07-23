import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
from backend.core.config import settings

def hash_password(password: str) -> str:
    """Hashes password securely with salt."""
    salt = "affiliate_cashback_production_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password against stored hash."""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates JWT token."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])

REVOKED_TOKENS = set()

def revoke_token(token: str) -> None:
    """Adds JWT token to revocation blacklist."""
    if token:
        REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    """Checks if JWT token has been revoked."""
    return token in REVOKED_TOKENS
