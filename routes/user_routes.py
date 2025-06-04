"""
User API routes for FIST Content Moderation System.

This module contains all user-related API endpoints including
registration, login, token management, and usage statistics.
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session

from core.models import (
    UserCreateRequest, UserResponse, UserLoginRequest, UserLoginResponse,
    TokenCreateRequest, TokenResponse, UsageStatsResponse
)
from core.type_adapters import convert_user, convert_token, convert_tokens_list
from core.database import get_db, DatabaseOperations
from core.auth import (
    get_password_hash, verify_password, create_user_access_token,
    generate_api_token, hash_token, verify_user_token
)
from core.config import Config

# Create user router
router = APIRouter(prefix="/api/user", tags=["User Management"])


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if registration requires invitation code
    if Config.REQUIRE_INVITATION_CODE:
        if not request.invitation_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation code is required for registration"
            )

        # Verify invitation code
        is_valid, error_message = DatabaseOperations.validate_invitation_code(db, request.invitation_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

    # Check user limit
    current_user_count = DatabaseOperations.get_user_count(db)
    if current_user_count >= Config.MAX_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of users reached"
        )

    # Check if username already exists
    existing_user = DatabaseOperations.get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create user
    password_hash = get_password_hash(request.password)
    user = DatabaseOperations.create_user(db, request.username, password_hash)

    # Use invitation code if provided
    if Config.REQUIRE_INVITATION_CODE and request.invitation_code:
        DatabaseOperations.use_invitation_code(db, request.invitation_code)

    return convert_user(user)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Login a user and return access token."""
    # Verify user credentials
    user = DatabaseOperations.get_user_by_username(db, request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not DatabaseOperations.is_user_active(user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )

    if not verify_password(request.password, user.password_hash):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Create access token
    access_token_expires = timedelta(minutes=Config.USER_TOKEN_EXPIRE_MINUTES)
    access_token = create_user_access_token(
        user_id=user.user_id,  # type: ignore
        expires_delta=access_token_expires
    )

    return UserLoginResponse(
        access_token=access_token,
        user=convert_user(user)
    )


def get_current_user_from_token(authorization: str = Header(None)) -> str:
    """Get current user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    user_id = verify_user_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user_id


@router.post("/tokens", response_model=TokenResponse)
async def create_token(
    request: TokenCreateRequest,
    user_id: str = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new API token for the user."""

    # Generate new token
    token = generate_api_token()
    token_hash = hash_token(token)

    # Store in database
    api_token = DatabaseOperations.create_api_token(
        db=db,
        user_id=user_id,
        name=request.name,
        token_hash=token_hash
    )

    return convert_token(api_token, include_token=True, token_value=token)


@router.get("/tokens", response_model=List[TokenResponse])
async def list_tokens(
    user_id: str = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all tokens for the user."""

    tokens = DatabaseOperations.get_user_tokens(db, user_id)

    return convert_tokens_list(tokens)


@router.delete("/tokens/{token_id}")
async def delete_token(
    token_id: str,
    user_id: str = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete an API token."""

    success = DatabaseOperations.deactivate_token(db, token_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )

    return {"message": "Token deleted successfully"}


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    user_id: str = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get usage statistics for the user."""

    stats = DatabaseOperations.get_user_usage_stats(db, user_id)

    return UsageStatsResponse(
        user_id=user_id,
        **stats
    )
