"""
Admin web interface routes for FIST Content Moderation System.

This module contains all web-based admin interface endpoints including
login, dashboard, configuration management, and records viewing.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import Config
from database import get_db, DatabaseOperations
from auth import get_current_user, require_auth, create_access_token, get_password_hash, verify_admin_credentials
from services import ModerationService

# Create admin router
router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Global moderation service instance
moderation_service = ModerationService()


@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request, user: Optional[str] = Depends(get_current_user)):
    """Admin login page or redirect to dashboard if already logged in."""
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Handle admin login."""
    # First try database authentication
    if verify_admin_credentials(db, username, password):
        # Create access token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="token",
            value=access_token,
            max_age=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True
        )
        return response

    # Fallback to config-based authentication for backward compatibility
    elif username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        # Create access token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="token",
            value=access_token,
            max_age=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True
        )
        return response

    # Authentication failed
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password"
    })


@router.get("/admin/logout")
async def admin_logout():
    """Handle admin logout."""
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("token")
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin dashboard page."""
    stats = DatabaseOperations.get_stats(db)
    recent_records = DatabaseOperations.get_all_moderation_records(db, limit=10)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "recent_records": recent_records
    })


@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin settings page (consolidated configuration and user management)."""
    # Get current user count
    current_user_count = DatabaseOperations.get_user_count(db)

    # Get users and invitation codes
    users = DatabaseOperations.get_all_users(db, limit=100)
    invitation_codes = DatabaseOperations.get_all_invitation_codes(db)

    # Get current configuration
    current_config: Dict[str, Any] = {
        "percentages": Config.DEFAULT_PERCENTAGES,
        "thresholds": Config.DEFAULT_THRESHOLDS,
        "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
        "ai_model": Config.AI_MODEL,
        "ai_base_url": Config.AI_BASE_URL,
        "ai_api_key": Config.AI_API_KEY,
        "max_users": Config.MAX_USERS
    }

    return templates.TemplateResponse("admin_settings.html", {
        "request": request,
        "user": user,
        "config": current_config,
        "current_user_count": current_user_count,
        "user_count": current_user_count,
        "max_users": Config.MAX_USERS,
        "users": users,
        "invitation_codes": invitation_codes,
        "require_invitation": Config.REQUIRE_INVITATION_CODE
    })

@router.get("/admin/config", response_class=HTMLResponse)
async def admin_config_page():
    """Admin configuration page (redirect to settings)."""
    return RedirectResponse(url="/admin/settings", status_code=302)


@router.post("/admin/config")
async def admin_update_config(
    request: Request,
    user: str = Depends(require_auth),
    db: Session = Depends(get_db),
    percentages: str = Form(...),
    thresholds: str = Form(...),
    low_threshold: int = Form(...),
    high_threshold: int = Form(...),
    ai_model: str = Form(...),
    ai_base_url: str = Form(...),
    ai_api_key: str = Form(...),
    max_users: int = Form(...)
):
    """Handle configuration updates."""
    try:
        # Parse and validate percentages
        new_percentages = [float(x.strip()) for x in percentages.split(",")]
        new_thresholds = [int(x.strip()) for x in thresholds.split(",")]

        # Get current user count for validation
        current_user_count = DatabaseOperations.get_user_count(db)

        # Validate ranges
        if not all(0 <= p <= 1 for p in new_percentages):
            raise ValueError("Percentages must be between 0 and 1")
        if not all(t > 0 for t in new_thresholds):
            raise ValueError("Thresholds must be positive")
        if not (0 <= low_threshold <= 100 and 0 <= high_threshold <= 100):
            raise ValueError("Probability thresholds must be between 0 and 100")
        if low_threshold >= high_threshold:
            raise ValueError("Low threshold must be less than high threshold")
        if not (1 <= max_users <= 10000):
            raise ValueError("Maximum users must be between 1 and 10000")
        if max_users < current_user_count:
            raise ValueError(f"Maximum users ({max_users}) cannot be less than current user count ({current_user_count})")

        # Update configuration in database
        config_updates = [
            ("percentages", str(new_percentages)),
            ("thresholds", str(new_thresholds)),
            ("probability_thresholds", f'{{"low": {low_threshold}, "high": {high_threshold}}}'),
            ("ai_model", ai_model),
            ("ai_base_url", ai_base_url),
            ("ai_api_key", ai_api_key),
            ("max_users", str(max_users))
        ]

        for key, value in config_updates:
            DatabaseOperations.set_config_value(db, key, value, user)

        # Update runtime configuration
        Config.DEFAULT_PERCENTAGES = new_percentages
        Config.DEFAULT_THRESHOLDS = new_thresholds
        Config.DEFAULT_PROBABILITY_THRESHOLDS = {"low": low_threshold, "high": high_threshold}
        Config.AI_MODEL = ai_model
        Config.AI_BASE_URL = ai_base_url
        Config.AI_API_KEY = ai_api_key
        Config.MAX_USERS = max_users

        # Update moderation service with new AI configuration
        global moderation_service
        moderation_service.update_ai_config(ai_api_key, ai_base_url, ai_model)

        # Get users and invitation codes for the template
        users = DatabaseOperations.get_all_users(db, limit=100)
        invitation_codes = DatabaseOperations.get_all_invitation_codes(db)

        return templates.TemplateResponse("admin_settings.html", {
            "request": request,
            "user": user,
            "config": {
                "percentages": new_percentages,
                "thresholds": new_thresholds,
                "probability_thresholds": {"low": low_threshold, "high": high_threshold},
                "ai_model": ai_model,
                "ai_base_url": ai_base_url,
                "ai_api_key": ai_api_key,
                "max_users": max_users
            },
            "current_user_count": current_user_count,
            "user_count": current_user_count,
            "max_users": max_users,
            "users": users,
            "invitation_codes": invitation_codes,
            "require_invitation": Config.REQUIRE_INVITATION_CODE,
            "success": "Configuration updated successfully!"
        })

    except Exception as e:
        # Get current user count for error response
        current_user_count = DatabaseOperations.get_user_count(db)

        # Get users and invitation codes for the template
        users = DatabaseOperations.get_all_users(db, limit=100)
        invitation_codes = DatabaseOperations.get_all_invitation_codes(db)

        return templates.TemplateResponse("admin_settings.html", {
            "request": request,
            "user": user,
            "config": {
                "percentages": Config.DEFAULT_PERCENTAGES,
                "thresholds": Config.DEFAULT_THRESHOLDS,
                "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
                "ai_model": Config.AI_MODEL,
                "ai_base_url": Config.AI_BASE_URL,
                "ai_api_key": Config.AI_API_KEY,
                "max_users": Config.MAX_USERS
            },
            "current_user_count": current_user_count,
            "user_count": current_user_count,
            "max_users": Config.MAX_USERS,
            "users": users,
            "invitation_codes": invitation_codes,
            "require_invitation": Config.REQUIRE_INVITATION_CODE,
            "error": f"Configuration update failed: {str(e)}"
        })


@router.get("/admin/records", response_class=HTMLResponse)
async def admin_records_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin records page."""
    records = DatabaseOperations.get_all_moderation_records(db, limit=100)

    return templates.TemplateResponse("records.html", {
        "request": request,
        "user": user,
        "records": records
    })


# User Management Routes
@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page():
    """Admin users management page (redirect to settings)."""
    return RedirectResponse(url="/admin/settings", status_code=302)


@router.post("/admin/users/create")
async def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        # Check user limit
        current_user_count = DatabaseOperations.get_user_count(db)
        if current_user_count >= Config.MAX_USERS:
            raise Exception("Maximum number of users reached")

        # Check if username already exists
        existing_user = DatabaseOperations.get_user_by_username(db, username)
        if existing_user:
            raise Exception("Username already exists")

        # Create user
        password_hash = get_password_hash(password)
        DatabaseOperations.create_user(db, username, password_hash)

        return RedirectResponse(url="/admin/settings?success=User created successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/settings?error={str(e)}", status_code=302)


@router.post("/admin/users/{user_id}/deactivate")
async def admin_deactivate_user(
    user_id: str,
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Deactivate a user."""
    try:
        success = DatabaseOperations.deactivate_user(db, user_id)
        if not success:
            raise Exception("User not found")

        return RedirectResponse(url="/admin/settings?success=User deactivated successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/settings?error={str(e)}", status_code=302)


# User password change functionality removed for security reasons
# Admin should not be able to change user passwords


@router.post("/admin/invitation-codes/create")
async def admin_create_invitation_code(
    request: Request,
    max_uses: Optional[int] = Form(None),
    expires_days: Optional[int] = Form(None),
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new invitation code."""
    try:
        # Generate random invitation code
        code = secrets.token_urlsafe(16)

        # Calculate expiration date
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        DatabaseOperations.create_invitation_code(
            db=db,
            code=code,
            created_by=user,
            expires_at=expires_at,
            max_uses=max_uses
        )

        return RedirectResponse(url="/admin/settings?success=Invitation code created successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/settings?error={str(e)}", status_code=302)


@router.post("/admin/invitation-codes/{code}/deactivate")
async def admin_deactivate_invitation_code(
    code: str,
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Deactivate an invitation code."""
    try:
        success = DatabaseOperations.deactivate_invitation_code(db, code)
        if not success:
            raise Exception("Invitation code not found")

        return RedirectResponse(url="/admin/settings?success=Invitation code deactivated successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/settings?error={str(e)}", status_code=302)


@router.post("/admin/change-password")
async def admin_change_own_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Change admin password."""
    try:
        # Verify current password against database first
        if not verify_admin_credentials(db, user, current_password):
            # Fallback to config-based verification for backward compatibility
            if user != Config.ADMIN_USERNAME or current_password != Config.ADMIN_PASSWORD:
                raise Exception("Current password is incorrect")

        # Validate new password
        if len(new_password) < 6:
            raise Exception("New password must be at least 6 characters long")

        # Hash the new password
        new_password_hash = get_password_hash(new_password)

        # Update admin password in database
        success = DatabaseOperations.update_admin_password(db, user, new_password_hash)

        if not success:
            # If admin doesn't exist in database, create them
            DatabaseOperations.create_admin(db, user, new_password_hash)

        return RedirectResponse(url="/admin/settings?success=Admin password changed successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/settings?error={str(e)}", status_code=302)
