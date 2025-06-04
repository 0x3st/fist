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
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fist.db")

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

    # Redis Cache Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Cache TTL in seconds (1 hour)
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "True").lower() == "true"

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Monitoring Configuration
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))

    # Batch Processing Configuration
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
    BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "300"))  # 5 minutes

    # Enhanced Text Analysis Configuration
    ENABLE_SENTIMENT_ANALYSIS = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "True").lower() == "true"
    ENABLE_TOPIC_EXTRACTION = os.getenv("ENABLE_TOPIC_EXTRACTION", "True").lower() == "true"
    ENABLE_TEXT_ANALYSIS = os.getenv("ENABLE_TEXT_ANALYSIS", "True").lower() == "true"

    # Sentiment Analysis Configuration
    SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "auto")  # auto, vader, textblob, transformers
    SENTIMENT_THRESHOLD_NEGATIVE = float(os.getenv("SENTIMENT_THRESHOLD_NEGATIVE", "-0.5"))
    SENTIMENT_THRESHOLD_POSITIVE = float(os.getenv("SENTIMENT_THRESHOLD_POSITIVE", "0.5"))

    # Topic Extraction Configuration
    MAX_TOPICS = int(os.getenv("MAX_TOPICS", "5"))
    MIN_TOPIC_CONFIDENCE = float(os.getenv("MIN_TOPIC_CONFIDENCE", "0.1"))

    # Text Quality Configuration
    MIN_QUALITY_SCORE = float(os.getenv("MIN_QUALITY_SCORE", "0.3"))
    MAX_SPAM_PROBABILITY = float(os.getenv("MAX_SPAM_PROBABILITY", "0.7"))

    # Language Processing Configuration
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
    ENABLE_MULTILINGUAL = os.getenv("ENABLE_MULTILINGUAL", "True").lower() == "true"

    # Dynamic Threshold Configuration
    REJECTION_THRESHOLD = float(os.getenv("REJECTION_THRESHOLD", "0.8"))
    MANUAL_REVIEW_THRESHOLD = float(os.getenv("MANUAL_REVIEW_THRESHOLD", "0.5"))