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
from auth import get_current_user, require_auth, create_access_token, get_password_hash
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
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login."""
    if username != Config.ADMIN_USERNAME or password != Config.ADMIN_PASSWORD:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

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


@router.get("/admin/config", response_class=HTMLResponse)
async def admin_config_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin configuration page."""
    # Get current user count
    current_user_count = DatabaseOperations.get_user_count(db)

    # Get current configuration
    current_config: Dict[str, Any] = {
        "percentages": Config.DEFAULT_PERCENTAGES,
        "thresholds": Config.DEFAULT_THRESHOLDS,
        "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
        "ai_model": Config.AI_MODEL,
        "max_users": Config.MAX_USERS
    }

    return templates.TemplateResponse("config.html", {
        "request": request,
        "user": user,
        "config": current_config,
        "current_user_count": current_user_count
    })


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
            ("max_users", str(max_users))
        ]

        for key, value in config_updates:
            DatabaseOperations.set_config_value(db, key, value, user)

        # Update runtime configuration
        Config.DEFAULT_PERCENTAGES = new_percentages
        Config.DEFAULT_THRESHOLDS = new_thresholds
        Config.DEFAULT_PROBABILITY_THRESHOLDS = {"low": low_threshold, "high": high_threshold}
        Config.AI_MODEL = ai_model
        Config.MAX_USERS = max_users

        # Reinitialize moderation service with new model
        global moderation_service
        moderation_service = ModerationService()

        return templates.TemplateResponse("config.html", {
            "request": request,
            "user": user,
            "config": {
                "percentages": new_percentages,
                "thresholds": new_thresholds,
                "probability_thresholds": {"low": low_threshold, "high": high_threshold},
                "ai_model": ai_model,
                "max_users": max_users
            },
            "current_user_count": current_user_count,
            "success": "Configuration updated successfully!"
        })

    except Exception as e:
        # Get current user count for error response
        current_user_count = DatabaseOperations.get_user_count(db)

        return templates.TemplateResponse("config.html", {
            "request": request,
            "user": user,
            "config": {
                "percentages": Config.DEFAULT_PERCENTAGES,
                "thresholds": Config.DEFAULT_THRESHOLDS,
                "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
                "ai_model": Config.AI_MODEL,
                "max_users": Config.MAX_USERS
            },
            "current_user_count": current_user_count,
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
async def admin_users_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin users management page."""
    users = DatabaseOperations.get_all_users(db, limit=100)
    user_count = DatabaseOperations.get_user_count(db)
    invitation_codes = DatabaseOperations.get_all_invitation_codes(db)

    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": user,
        "users": users,
        "user_count": user_count,
        "max_users": Config.MAX_USERS,
        "invitation_codes": invitation_codes,
        "require_invitation": Config.REQUIRE_INVITATION_CODE
    })


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

        return RedirectResponse(url="/admin/users?success=User created successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)


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

        return RedirectResponse(url="/admin/users?success=User deactivated successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)


@router.post("/admin/users/{user_id}/change-password")
async def admin_change_user_password(
    user_id: str,
    new_password: str = Form(...),
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        password_hash = get_password_hash(new_password)
        success = DatabaseOperations.update_user_password(db, user_id, password_hash)
        if not success:
            raise Exception("User not found")

        return RedirectResponse(url="/admin/users?success=Password changed successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)


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

        return RedirectResponse(url="/admin/users?success=Invitation code created successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)


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

        return RedirectResponse(url="/admin/users?success=Invitation code deactivated successfully", status_code=302)

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)


@router.post("/admin/change-password")
async def admin_change_own_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Change admin password."""
    try:
        # Verify current password
        if current_password != Config.ADMIN_PASSWORD:
            raise Exception("Current password is incorrect")

        # Update admin password in environment/config
        # Note: This would require updating the environment variable or config file
        # For now, we'll just show a message that this needs to be done manually
        raise Exception("Admin password change requires manual configuration update")

    except Exception as e:
        return RedirectResponse(url=f"/admin/users?error={str(e)}", status_code=302)
