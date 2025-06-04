"""
Admin API routes for FIST Content Moderation System.

This module contains all admin-related API endpoints including
admin login, user management, invitation code management, and system configuration.
"""
import secrets
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session

from core.models import (
    AdminLoginRequest, AdminLoginResponse, AdminUserListResponse,
    InvitationCodeCreateRequest, InvitationCodeResponse,
    UserLimitUpdateRequest, AIConfigUpdateRequest, AdminPasswordUpdateRequest,
    UserResponse
)
from core.type_adapters import convert_users_list, convert_invitation_codes_list
from core.database import get_db, DatabaseOperations
from core.auth import (
    verify_admin_credentials, create_admin_access_token, require_admin_auth,
    get_password_hash, verify_password
)
from core.config import Config

# Create admin router
router = APIRouter(prefix="/api/admin", tags=["Admin Management"])


async def get_authenticated_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """Get authenticated admin from admin token."""
    # Create a new dependency that properly injects the database
    return require_admin_auth(authorization, db)


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint."""
    # Verify admin credentials
    if not verify_admin_credentials(db, request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )

    # Get admin info
    admin = DatabaseOperations.get_admin_by_username(db, request.username)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )

    # Create access token
    access_token = create_admin_access_token(
        admin_id=admin.admin_id,  # type: ignore
        expires_delta=timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return AdminLoginResponse(
        access_token=access_token,
        admin_id=admin.admin_id,  # type: ignore
        username=admin.username  # type: ignore
    )


@router.get("/users", response_model=AdminUserListResponse)
async def get_all_users(
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Get all users for admin management."""
    users = DatabaseOperations.get_all_users(db)
    user_responses = convert_users_list(users)

    return AdminUserListResponse(
        users=user_responses,
        total_count=len(user_responses)
    )


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user."""
    success = DatabaseOperations.deactivate_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": "User deactivated successfully"}


@router.put("/user-limit")
async def update_user_limit(
    request: UserLimitUpdateRequest,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Update the maximum number of users allowed."""
    # Update in database
    success = DatabaseOperations.set_config_value(
        db=db,
        config_key="max_users",
        config_value=str(request.max_users),
        updated_by=f"admin:{admin_id}"
    )

    if success:
        # Update in-memory config
        Config.MAX_USERS = request.max_users
        return {"message": f"User limit updated to {request.max_users}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user limit"
        )


@router.post("/invitation-codes", response_model=InvitationCodeResponse)
async def create_invitation_code(
    request: InvitationCodeCreateRequest,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Create a new invitation code."""
    # Generate a random invitation code
    code = "inv_" + secrets.token_urlsafe(16)

    # Create invitation code
    invitation = DatabaseOperations.create_invitation_code(
        db=db,
        code=code,
        created_by=f"admin:{admin_id}",
        expires_at=request.expires_at,
        max_uses=request.max_uses
    )

    return InvitationCodeResponse(
        code=invitation.code,  # type: ignore
        created_at=invitation.created_at,  # type: ignore
        expires_at=invitation.expires_at,  # type: ignore
        max_uses=invitation.max_uses,  # type: ignore
        current_uses=invitation.current_uses,  # type: ignore
        is_active=bool(invitation.is_active)  # type: ignore
    )


@router.get("/invitation-codes", response_model=List[InvitationCodeResponse])
async def get_invitation_codes(
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Get all invitation codes."""
    codes = DatabaseOperations.get_all_invitation_codes(db)
    return convert_invitation_codes_list(codes)


@router.delete("/invitation-codes/{code}")
async def deactivate_invitation_code(
    code: str,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Deactivate an invitation code."""
    success = DatabaseOperations.deactivate_invitation_code(db, code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation code not found"
        )

    return {"message": "Invitation code deactivated successfully"}


@router.put("/ai-config")
async def update_ai_config(
    request: AIConfigUpdateRequest,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Update AI configuration."""
    updated_fields = []

    if request.ai_api_key is not None:
        success = DatabaseOperations.set_config_value(
            db=db,
            config_key="ai_api_key",
            config_value=request.ai_api_key,
            updated_by=f"admin:{admin_id}"
        )
        if success:
            Config.AI_API_KEY = request.ai_api_key
            updated_fields.append("ai_api_key")

    if request.ai_base_url is not None:
        success = DatabaseOperations.set_config_value(
            db=db,
            config_key="ai_base_url",
            config_value=request.ai_base_url,
            updated_by=f"admin:{admin_id}"
        )
        if success:
            Config.AI_BASE_URL = request.ai_base_url
            updated_fields.append("ai_base_url")

    if request.ai_model is not None:
        success = DatabaseOperations.set_config_value(
            db=db,
            config_key="ai_model",
            config_value=request.ai_model,
            updated_by=f"admin:{admin_id}"
        )
        if success:
            Config.AI_MODEL = request.ai_model
            updated_fields.append("ai_model")

    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )

    return {
        "message": f"AI configuration updated: {', '.join(updated_fields)}",
        "updated_fields": updated_fields
    }


@router.put("/password")
async def update_admin_password(
    request: AdminPasswordUpdateRequest,
    admin_id: str = Depends(get_authenticated_admin),
    db: Session = Depends(get_db)
):
    """Update admin password."""
    # Get current admin
    admin = DatabaseOperations.get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    # Verify current password
    if not verify_password(request.current_password, admin.password_hash):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Update password
    new_password_hash = get_password_hash(request.new_password)
    success = DatabaseOperations.update_admin_password(
        db=db,
        username=admin.username,  # type: ignore
        new_password_hash=new_password_hash
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    return {"message": "Password updated successfully"}
