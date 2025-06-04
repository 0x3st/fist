"""
Data models for FIST Content Moderation System.

This module contains all Pydantic models for API requests/responses
and SQLAlchemy models for database tables.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# SQLAlchemy Base
Base = declarative_base()


# Pydantic Models for API
class ModerationRequest(BaseModel):
    """Request model for content moderation."""
    content: str = Field(..., description="Content to be moderated", min_length=1)
    percentages: Optional[List[float]] = Field(None, description="Custom percentages for content piercing")
    thresholds: Optional[List[int]] = Field(None, description="Custom word count thresholds")
    probability_thresholds: Optional[Dict[str, int]] = Field(None, description="Custom probability thresholds for decision making")


class AIResult(BaseModel):
    """AI moderation result model."""
    inappropriate_probability: int = Field(..., description="Probability (0-100) that content is inappropriate")
    reason: str = Field(..., description="Brief explanation of the assessment")


class SentimentAnalysisResult(BaseModel):
    """Sentiment analysis result model."""
    score: float = Field(..., description="Sentiment score (-1.0 to 1.0)")
    confidence: float = Field(..., description="Confidence level (0.0 to 1.0)")
    label: str = Field(..., description="Sentiment label (positive, negative, neutral)")
    backend: str = Field(..., description="Analysis backend used")


class TopicExtractionResult(BaseModel):
    """Topic extraction result model."""
    primary_topic: str = Field(..., description="Primary topic identified")
    topic_confidence: float = Field(..., description="Confidence in primary topic")
    all_topics: List[Dict[str, float]] = Field(..., description="All topics with confidence scores")
    keywords: List[str] = Field(..., description="Extracted keywords")
    categories: List[str] = Field(..., description="Content categories")
    content_type: str = Field(..., description="Detected content type")
    language: str = Field(..., description="Detected language")


class TextQualityResult(BaseModel):
    """Text quality analysis result model."""
    quality_score: float = Field(..., description="Overall quality score (0.0 to 1.0)")
    readability_level: str = Field(..., description="Readability level")
    complexity_score: float = Field(..., description="Text complexity score")
    spam_probability: float = Field(..., description="Spam probability (0.0 to 1.0)")
    spelling_errors: int = Field(..., description="Number of spelling errors detected")


class EnhancedModerationResult(BaseModel):
    """Enhanced moderation result with advanced analysis."""
    moderation_id: str = Field(..., description="Unique identifier for this moderation")
    content_hash: str = Field(..., description="SHA-256 hash of content for verification")
    ai_result: AIResult = Field(..., description="AI assessment result")
    final_decision: str = Field(..., description="Final decision: A (Approved), R (Rejected), M (Manual review)")
    reason: str = Field(..., description="Explanation for the final decision")
    created_at: datetime = Field(..., description="Timestamp when moderation was performed")
    word_count: int = Field(..., description="Word count of original content")
    percentage_used: float = Field(..., description="Percentage of content that was analyzed")

    # Enhanced analysis results
    sentiment_analysis: Optional[SentimentAnalysisResult] = Field(None, description="Sentiment analysis results")
    topic_extraction: Optional[TopicExtractionResult] = Field(None, description="Topic extraction results")
    text_quality: Optional[TextQualityResult] = Field(None, description="Text quality analysis results")
    analysis_confidence: float = Field(..., description="Overall analysis confidence")


class ModerationResult(BaseModel):
    """Final moderation result model - privacy focused."""
    moderation_id: str = Field(..., description="Unique identifier for this moderation")
    content_hash: str = Field(..., description="SHA-256 hash of content for verification")
    ai_result: AIResult = Field(..., description="AI assessment result")
    final_decision: str = Field(..., description="Final decision: A (Approved), R (Rejected), M (Manual review)")
    reason: str = Field(..., description="Explanation for the final decision")
    created_at: datetime = Field(..., description="Timestamp when moderation was performed")
    word_count: int = Field(..., description="Word count of original content")
    percentage_used: float = Field(..., description="Percentage of content that was analyzed")


class ModerationResponse(BaseModel):
    """Response model for moderation request."""
    moderation_id: str = Field(..., description="Unique identifier for this moderation")
    status: str = Field(..., description="Status of the moderation")
    result: Optional[ModerationResult] = Field(None, description="Moderation result if completed")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")


# User Management Models
class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""
    username: str = Field(..., description="Username", min_length=3, max_length=50)
    password: str = Field(..., description="Password", min_length=6)
    invitation_code: Optional[str] = Field(None, description="Invitation code for registration")


class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="User creation timestamp")
    is_active: bool = Field(..., description="Whether user is active")


class TokenCreateRequest(BaseModel):
    """Request model for creating a new API token."""
    name: str = Field(..., description="Token name/description", max_length=100)


class TokenResponse(BaseModel):
    """Response model for API token information."""
    token_id: str = Field(..., description="Token UUID")
    name: str = Field(..., description="Token name/description")
    token: Optional[str] = Field(None, description="Token value (only shown on creation)")
    created_at: datetime = Field(..., description="Token creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(..., description="Number of times this token has been used")
    is_active: bool = Field(..., description="Whether token is active")


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserLoginResponse(BaseModel):
    """Response model for user login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class UsageStatsResponse(BaseModel):
    """Response model for user usage statistics - privacy focused."""
    user_id: str = Field(..., description="User UUID")
    tokens_count: int = Field(..., description="Number of active tokens")


class InvitationCodeResponse(BaseModel):
    """Response model for invitation code."""
    code: str = Field(..., description="Invitation code")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    max_uses: Optional[int] = Field(None, description="Maximum number of uses")
    current_uses: int = Field(..., description="Current number of uses")
    is_active: bool = Field(..., description="Whether code is active")


# Admin Management Models
class AdminLoginRequest(BaseModel):
    """Request model for admin login."""
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class AdminLoginResponse(BaseModel):
    """Response model for admin login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    admin_id: str = Field(..., description="Admin UUID")
    username: str = Field(..., description="Admin username")


class AdminUserListResponse(BaseModel):
    """Response model for admin user list."""
    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")


class InvitationCodeCreateRequest(BaseModel):
    """Request model for creating invitation codes."""
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    max_uses: Optional[int] = Field(None, description="Maximum number of uses")


class UserLimitUpdateRequest(BaseModel):
    """Request model for updating user limit."""
    max_users: int = Field(..., description="Maximum number of users allowed", ge=1)


class AIConfigUpdateRequest(BaseModel):
    """Request model for updating AI configuration."""
    ai_api_key: Optional[str] = Field(None, description="AI API key")
    ai_base_url: Optional[str] = Field(None, description="AI base URL")
    ai_model: Optional[str] = Field(None, description="AI model name")


class AdminPasswordUpdateRequest(BaseModel):
    """Request model for updating admin password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=6)


# Batch Processing Models
class BatchModerationRequest(BaseModel):
    """Request model for batch content moderation."""
    contents: List[str] = Field(..., description="List of content to be moderated", min_length=1, max_length=100)
    percentages: Optional[List[float]] = Field(None, description="Custom percentages for content piercing")
    thresholds: Optional[List[int]] = Field(None, description="Custom word count thresholds")
    probability_thresholds: Optional[Dict[str, int]] = Field(None, description="Custom probability thresholds for decision making")
    background: bool = Field(False, description="Process in background (for large batches)")


class BatchModerationResponse(BaseModel):
    """Response model for batch content moderation."""
    job_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    total_items: int = Field(..., description="Total number of items in the batch")
    processed_items: int = Field(0, description="Number of items processed so far")
    progress_percent: float = Field(0.0, description="Processing progress percentage")
    results: Optional[List[ModerationResult]] = Field(None, description="Moderation results (if completed)")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Processing errors")
    created_at: datetime = Field(..., description="When the job was created")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    background_task_id: Optional[str] = Field(None, description="Background task ID (if processed in background)")


class BatchJobStatusResponse(BaseModel):
    """Response model for batch job status."""
    job_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Job status")
    total_items: int = Field(..., description="Total number of items")
    processed_items: int = Field(..., description="Number of items processed")
    progress_percent: float = Field(..., description="Processing progress percentage")
    elapsed_time_seconds: Optional[float] = Field(None, description="Elapsed processing time")
    estimated_remaining_seconds: Optional[float] = Field(None, description="Estimated remaining time")
    errors_count: int = Field(0, description="Number of errors encountered")


# Monitoring and Health Check Models
class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Overall health status: healthy, warning, unhealthy")
    timestamp: str = Field(..., description="Health check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual component health checks")


class MetricsResponse(BaseModel):
    """Response model for system metrics."""
    enabled: bool = Field(..., description="Whether metrics collection is enabled")
    uptime_seconds: Optional[int] = Field(None, description="System uptime in seconds")
    requests: Optional[Dict[str, Any]] = Field(None, description="Request metrics")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    system: Optional[Dict[str, Any]] = Field(None, description="System resource metrics")
    cache: Optional[Dict[str, Any]] = Field(None, description="Cache performance metrics")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    enabled: bool = Field(..., description="Whether cache is enabled")
    connected: Optional[bool] = Field(None, description="Whether cache is connected")
    keys_count: Optional[int] = Field(None, description="Number of cached keys")
    memory_used: Optional[str] = Field(None, description="Memory used by cache")
    hits: Optional[int] = Field(None, description="Cache hits")
    misses: Optional[int] = Field(None, description="Cache misses")
    hit_rate: Optional[float] = Field(None, description="Cache hit rate percentage")


# SQLAlchemy Database Models
class User(Base):
    """Database model for users."""
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    # Relationships
    tokens = relationship("APIToken", back_populates="user")


class APIToken(Base):
    """Database model for API tokens."""
    __tablename__ = "api_tokens"

    token_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(100), nullable=False)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="tokens")


class InvitationCode(Base):
    """Database model for invitation codes."""
    __tablename__ = "invitation_codes"

    code = Column(String(50), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=False)


class ModerationRecord(Base):
    """Database model for moderation records - privacy focused."""
    __tablename__ = "moderation_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Store only hash of content for verification, not actual content
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash
    word_count = Column(Integer, nullable=False)
    percentage_used = Column(Float, nullable=False)  # type: ignore
    inappropriate_probability = Column(Integer, nullable=False)
    final_decision = Column(String(1), nullable=False)  # A, R, M
    created_at = Column(DateTime, default=datetime.now)


class Admin(Base):
    """Database model for admin credentials."""
    __tablename__ = "admins"

    admin_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)


class ConfigRecord(Base):
    """Database model for system configuration."""
    __tablename__ = "config_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String(100), nullable=False)


class SentimentRecord(Base):
    """Database model for sentiment analysis results."""
    __tablename__ = "sentiment_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    moderation_id = Column(String, ForeignKey("moderation_records.id"), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    sentiment_confidence = Column(Float, nullable=False)
    sentiment_label = Column(String(20), nullable=False)
    backend_used = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class TopicRecord(Base):
    """Database model for topic extraction results."""
    __tablename__ = "topic_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    moderation_id = Column(String, ForeignKey("moderation_records.id"), nullable=False)
    primary_topic = Column(String(100), nullable=False)
    topic_confidence = Column(Float, nullable=False)
    keywords = Column(Text, nullable=True)  # JSON string of keywords
    categories = Column(Text, nullable=True)  # JSON string of categories
    content_type = Column(String(50), nullable=False)
    detected_language = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class TextQualityRecord(Base):
    """Database model for text quality analysis results."""
    __tablename__ = "text_quality_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    moderation_id = Column(String, ForeignKey("moderation_records.id"), nullable=False)
    quality_score = Column(Float, nullable=False)
    readability_level = Column(String(20), nullable=False)
    complexity_score = Column(Float, nullable=False)
    spam_probability = Column(Float, nullable=False)
    spelling_errors = Column(Integer, nullable=False)
    analysis_confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
