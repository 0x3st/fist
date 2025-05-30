"""
User web interface routes for FIST Content Moderation System.

This module contains all web-based user interface endpoints including
login, dashboard, token management, and user settings.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import Config
from database import get_db, DatabaseOperations
from auth import (
    get_password_hash, verify_password, create_user_access_token,
    generate_api_token, hash_token, verify_user_token
)

# Create user web router
router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="templates")


def get_current_user_from_cookie(token: Optional[str] = None):
    """Get current authenticated user from cookie."""
    if not token:
        return None
    user_id = verify_user_token(token)
    return user_id


def require_user_auth(request: Request):
    """Require user authentication for user endpoints."""
    token = request.cookies.get("user_token")
    user_id = get_current_user_from_cookie(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
    return user_id


@router.get("/user", response_class=HTMLResponse)
async def user_login_page(request: Request):
    """User login/register page."""
    user_id = get_current_user_from_cookie(request.cookies.get("user_token"))
    if user_id:
        return RedirectResponse(url="/user/dashboard", status_code=302)
    return templates.TemplateResponse("user_login.html", {"request": request})


@router.post("/user/login")
async def user_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user login."""
    try:
        # Verify user credentials
        user = DatabaseOperations.get_user_by_username(db, username)
        if not user:
            raise Exception("Invalid username or password")

        if not DatabaseOperations.is_user_active(user):
            raise Exception("User account is deactivated")

        if not verify_password(password, user.password_hash):  # type: ignore
            raise Exception("Invalid username or password")

        # Create access token
        access_token_expires = timedelta(minutes=Config.USER_TOKEN_EXPIRE_MINUTES)
        access_token = create_user_access_token(
            user_id=user.user_id,  # type: ignore
            expires_delta=access_token_expires
        )

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/user/dashboard", status_code=302)
        response.set_cookie(
            key="user_token",
            value=access_token,
            max_age=Config.USER_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True
        )
        return response

    except Exception as e:
        return templates.TemplateResponse("user_login.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/user/register")
async def user_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invitation_code: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Handle user registration."""
    try:
        # Check if registration requires invitation code
        if Config.REQUIRE_INVITATION_CODE:
            if not invitation_code:
                raise Exception("Invitation code is required for registration")

            # Verify invitation code
            is_valid, error_message = DatabaseOperations.validate_invitation_code(db, invitation_code)
            if not is_valid:
                raise Exception(error_message)

        # Check user limit
        current_user_count = DatabaseOperations.get_user_count(db)
        if current_user_count >= Config.MAX_USERS:
            raise Exception("Maximum number of users reached")

        # Check if username already exists
        existing_user = DatabaseOperations.get_user_by_username(db, username)
        if existing_user:
            raise Exception("Username already exists")

        # Validate password
        if len(password) < 6:
            raise Exception("Password must be at least 6 characters long")

        # Create user
        password_hash = get_password_hash(password)
        user = DatabaseOperations.create_user(db, username, password_hash)

        # Use invitation code if provided
        if Config.REQUIRE_INVITATION_CODE and invitation_code:
            DatabaseOperations.use_invitation_code(db, invitation_code)

        # Create access token
        access_token_expires = timedelta(minutes=Config.USER_TOKEN_EXPIRE_MINUTES)
        access_token = create_user_access_token(
            user_id=user.user_id,  # type: ignore
            expires_delta=access_token_expires
        )

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/user/dashboard?success=Registration successful! Welcome to FIST.", status_code=302)
        response.set_cookie(
            key="user_token",
            value=access_token,
            max_age=Config.USER_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True
        )
        return response

    except Exception as e:
        return templates.TemplateResponse("user_login.html", {
            "request": request,
            "error": str(e),
            "show_register": True
        })


@router.get("/user/logout")
async def user_logout():
    """Handle user logout."""
    response = RedirectResponse(url="/user", status_code=302)
    response.delete_cookie("user_token")
    return response


@router.get("/user/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request, db: Session = Depends(get_db)):
    """User dashboard page."""
    try:
        user_id = require_user_auth(request)
        user = DatabaseOperations.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user statistics
        usage_stats = DatabaseOperations.get_user_usage_stats(db, user_id)
        tokens = DatabaseOperations.get_user_tokens(db, user_id)
        recent_records = DatabaseOperations.get_user_moderation_records(db, user_id, limit=10)

        return templates.TemplateResponse("user_dashboard.html", {
            "request": request,
            "user": user,
            "usage_stats": usage_stats,
            "tokens": tokens,
            "recent_records": recent_records
        })

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)
    except Exception:
        return RedirectResponse(url="/user", status_code=302)


@router.get("/user/tokens", response_class=HTMLResponse)
async def user_tokens_page(request: Request, db: Session = Depends(get_db)):
    """User tokens management page."""
    try:
        user_id = require_user_auth(request)
        user = DatabaseOperations.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tokens = DatabaseOperations.get_user_tokens(db, user_id)

        return templates.TemplateResponse("user_tokens.html", {
            "request": request,
            "user": user,
            "tokens": tokens
        })

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)


@router.post("/user/tokens/create")
async def user_create_token(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new API token for the user."""
    try:
        user_id = require_user_auth(request)

        # Validate token name
        if len(name.strip()) < 3:
            raise Exception("Token name must be at least 3 characters long")

        # Generate new token
        token = generate_api_token()
        token_hash = hash_token(token)

        # Store in database
        api_token = DatabaseOperations.create_api_token(
            db=db,
            user_id=user_id,
            name=name.strip(),
            token_hash=token_hash
        )

        return RedirectResponse(
            url=f"/user/tokens?success=Token '{name}' created successfully&new_token={token}",
            status_code=302
        )

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)
    except Exception as e:
        return RedirectResponse(url=f"/user/tokens?error={str(e)}", status_code=302)


@router.post("/user/tokens/{token_id}/delete")
async def user_delete_token(
    token_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete an API token."""
    try:
        user_id = require_user_auth(request)

        success = DatabaseOperations.deactivate_token(db, token_id, user_id)
        if not success:
            raise Exception("Token not found or access denied")

        return RedirectResponse(url="/user/tokens?success=Token deleted successfully", status_code=302)

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)
    except Exception as e:
        return RedirectResponse(url=f"/user/tokens?error={str(e)}", status_code=302)


@router.get("/user/settings", response_class=HTMLResponse)
async def user_settings_page(request: Request, db: Session = Depends(get_db)):
    """User settings page."""
    try:
        user_id = require_user_auth(request)
        user = DatabaseOperations.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return templates.TemplateResponse("user_settings.html", {
            "request": request,
            "user": user
        })

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)


@router.post("/user/change-password")
async def user_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        user_id = require_user_auth(request)
        user = DatabaseOperations.get_user_by_id(db, user_id)
        if not user:
            raise Exception("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):  # type: ignore
            raise Exception("Current password is incorrect")

        # Validate new password
        if len(new_password) < 6:
            raise Exception("New password must be at least 6 characters long")

        if new_password != confirm_password:
            raise Exception("New passwords do not match")

        # Update password
        new_password_hash = get_password_hash(new_password)
        success = DatabaseOperations.update_user_password(db, user_id, new_password_hash)

        if not success:
            raise Exception("Failed to update password")

        return RedirectResponse(url="/user/settings?success=Password changed successfully", status_code=302)

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)
    except Exception as e:
        return RedirectResponse(url=f"/user/settings?error={str(e)}", status_code=302)


@router.get("/user/history", response_class=HTMLResponse)
async def user_history_page(request: Request, db: Session = Depends(get_db)):
    """User moderation history page."""
    try:
        user_id = require_user_auth(request)
        user = DatabaseOperations.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get pagination parameters
        page = int(request.query_params.get("page", 1))
        limit = 20
        offset = (page - 1) * limit

        records = DatabaseOperations.get_user_moderation_records(db, user_id, limit=limit, offset=offset)
        total_records = DatabaseOperations.get_user_moderation_count(db, user_id)
        total_pages = (total_records + limit - 1) // limit

        return templates.TemplateResponse("user_history.html", {
            "request": request,
            "user": user,
            "records": records,
            "current_page": page,
            "total_pages": total_pages,
            "total_records": total_records
        })

    except HTTPException:
        return RedirectResponse(url="/user", status_code=302)
