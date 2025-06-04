"""
Core business logic for FIST Content Moderation System.

This package contains the fundamental components:
- Configuration management
- Database operations
- Data models
- Authentication
- Main moderation service
"""

from .config import Config
from .database import get_db, DatabaseOperations, create_tables
from .models import *
from .auth import require_api_auth, create_access_token, verify_password

# Lazy import to avoid circular dependency
def get_moderation_service():
    """Get ModerationService instance (lazy import)."""
    from .moderation import ModerationService
    return ModerationService()

__all__ = [
    'Config',
    'get_db', 'DatabaseOperations', 'create_tables',
    'require_api_auth', 'create_access_token', 'verify_password',
    'get_moderation_service'
]
