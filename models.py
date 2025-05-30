"""
Data models for FIST Content Moderation System.

This module contains all Pydantic models for API requests/responses
and SQLAlchemy models for database tables.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict
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


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")


# Statistics removed for privacy protection


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
    # Individual token usage is shown in TokenResponse.usage_count


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

    # No user relationship for privacy - tokens handle their own usage tracking


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
