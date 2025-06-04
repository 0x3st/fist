"""
Authentication module for FIST Content Moderation System.

This module handles all authentication-related functionality including
password hashing, JWT token creation/verification, and authentication dependencies.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Cookie, Header, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import Config

# Authentication setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def verify_admin_credentials(db: Session, username: str, password: str) -> bool:
    """Verify admin credentials against database."""
    from database import DatabaseOperations

    admin = DatabaseOperations.get_admin_by_username(db, username)
    if not admin:
        return False

    return verify_password(password, admin.password_hash)  # type: ignore


def get_current_user(token: str = Cookie(None)):
    """Get current authenticated user from cookie."""
    if not token:
        return None
    username = verify_token(token)
    # For backward compatibility, still check config admin username
    # but in production, this should be validated against database
    if username != Config.ADMIN_USERNAME:
        return None
    return username


def require_auth(token: str = Cookie(None)):
    """Require authentication for admin endpoints."""
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


# API Token Management
def generate_api_token() -> str:
    """Generate a new API token."""
    return Config.API_TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash an API token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_api_token(db: Session, token: str) -> Optional[str]:
    """Verify an API token and return the user_id if valid."""
    from database import DatabaseOperations

    if not token.startswith(Config.API_TOKEN_PREFIX):
        return None

    token_hash = hash_token(token)
    api_token = DatabaseOperations.get_token_by_hash(db, token_hash)

    if api_token and api_token.user and api_token.user.is_active:
        # Update last used timestamp
        DatabaseOperations.update_token_last_used(db, api_token.token_id)
        return api_token.user_id

    return None


def require_api_auth(
    authorization: str = Header(None),
    db: Session = Depends(lambda: None)  # Will be properly injected from get_db
) -> str:
    """Require API token authentication."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API token required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    user_id = verify_api_token(db, token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_id


def create_user_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for user sessions."""
    to_encode = {"sub": user_id, "type": "user"}
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=Config.USER_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


def verify_user_token(token: str) -> Optional[str]:
    """Verify a user JWT token and return the user_id."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if user_id is None or token_type != "user":
            return None
        return user_id
    except JWTError:
        return None


def create_admin_access_token(admin_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for admin sessions."""
    to_encode = {"sub": admin_id, "type": "admin"}
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


def verify_admin_token(token: str) -> Optional[str]:
    """Verify an admin JWT token and return the admin_id."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        admin_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if admin_id is None or token_type != "admin":
            return None
        return admin_id
    except JWTError:
        return None


def require_admin_auth(
    authorization: str = Header(None),
    db: Session = Depends(lambda: None)  # Will be properly injected from get_db
) -> str:
    """Require admin authentication for admin endpoints."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid admin token required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    admin_id = verify_admin_token(token)
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid admin token required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify admin still exists and is active
    from database import DatabaseOperations
    admin = DatabaseOperations.get_admin_by_id(db, admin_id)
    if not admin or not bool(admin.is_active):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return admin_id
