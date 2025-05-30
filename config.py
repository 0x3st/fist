"""
Configuration module for FIST Content Moderation System.

This module contains all configuration settings and environment variables
used throughout the application.
"""
import os
from typing import List, Dict


class Config:
    """Configuration class for FIST system."""

    # Database Configuration
    DATABASE_URL = "sqlite:///./fist.db"

    # AI Configuration
    AI_API_KEY = os.getenv("AI_API_KEY", "sk-488d88049a9440a591bb948fa8fea5ca")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")

    # Content Moderation Configuration
    DEFAULT_PERCENTAGES: List[float] = [0.8, 0.6, 0.4, 0.2]
    DEFAULT_THRESHOLDS: List[int] = [500, 1000, 3000]
    DEFAULT_PROBABILITY_THRESHOLDS: Dict[str, int] = {"low": 20, "high": 80}

    # API Server Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Admin Authentication Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "fist-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in production!

    # User Management Configuration
    MAX_USERS = int(os.getenv("MAX_USERS", "100"))  # Maximum number of users allowed
    REQUIRE_INVITATION_CODE = os.getenv("REQUIRE_INVITATION_CODE", "True").lower() == "true"
    USER_TOKEN_EXPIRE_MINUTES = int(os.getenv("USER_TOKEN_EXPIRE_MINUTES", "60"))  # User session token expiry
    API_TOKEN_PREFIX = "fist_"  # Prefix for API tokens