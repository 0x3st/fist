"""
API Routes for FIST Content Moderation System.

This package contains all API route handlers:
- Main API routes for content moderation
- Admin routes for system management
- User routes for user management
"""

from .api_routes import router as api_router
from .admin_routes import router as admin_router
from .user_routes import router as user_router

__all__ = ['api_router', 'admin_router', 'user_router']
