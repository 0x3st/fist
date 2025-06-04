"""
Type adapters for SQLAlchemy 2.0 and Pydantic v2 integration.

This module provides clean type conversion between SQLAlchemy models
and Pydantic models, addressing the type annotation issues in modern versions.
"""

from datetime import datetime
from typing import Any, Optional, List
from sqlalchemy.orm import DeclarativeBase

from .models import (
    ModerationResult, AIResult, UserResponse, TokenResponse, 
    InvitationCodeResponse, ModerationRecord, User, APIToken, InvitationCode
)


class SQLAlchemyAdapter:
    """Adapter for converting SQLAlchemy models to Pydantic models."""
    
    @staticmethod
    def moderation_record_to_result(record: ModerationRecord) -> ModerationResult:
        """Convert SQLAlchemy ModerationRecord to Pydantic ModerationResult."""
        return ModerationResult(
            moderation_id=str(record.id),
            content_hash=str(record.content_hash),
            ai_result=AIResult(
                inappropriate_probability=int(record.inappropriate_probability),
                reason="AI analysis completed"
            ),
            final_decision=str(record.final_decision),
            reason="Decision based on AI analysis",
            created_at=record.created_at,
            word_count=int(record.word_count),
            percentage_used=float(record.percentage_used)
        )
    
    @staticmethod
    def user_to_response(user: User) -> UserResponse:
        """Convert SQLAlchemy User to Pydantic UserResponse."""
        return UserResponse(
            user_id=str(user.user_id),
            username=str(user.username),
            created_at=user.created_at,
            is_active=bool(user.is_active)
        )
    
    @staticmethod
    def token_to_response(token: APIToken, include_token: bool = False, token_value: Optional[str] = None) -> TokenResponse:
        """Convert SQLAlchemy APIToken to Pydantic TokenResponse."""
        return TokenResponse(
            token_id=str(token.token_id),
            name=str(token.name),
            token=token_value if include_token else None,
            created_at=token.created_at,
            last_used=token.last_used,
            usage_count=int(token.usage_count or 0),
            is_active=bool(token.is_active)
        )
    
    @staticmethod
    def invitation_code_to_response(code: InvitationCode) -> InvitationCodeResponse:
        """Convert SQLAlchemy InvitationCode to Pydantic InvitationCodeResponse."""
        return InvitationCodeResponse(
            code=str(code.code),
            created_at=code.created_at,
            expires_at=code.expires_at,
            max_uses=int(code.max_uses) if code.max_uses is not None else None,
            current_uses=int(code.current_uses or 0),
            is_active=bool(code.is_active)
        )
    
    @staticmethod
    def users_to_response_list(users: List[User]) -> List[UserResponse]:
        """Convert list of SQLAlchemy Users to list of Pydantic UserResponses."""
        return [SQLAlchemyAdapter.user_to_response(user) for user in users]
    
    @staticmethod
    def tokens_to_response_list(tokens: List[APIToken]) -> List[TokenResponse]:
        """Convert list of SQLAlchemy APITokens to list of Pydantic TokenResponses."""
        return [SQLAlchemyAdapter.token_to_response(token) for token in tokens]
    
    @staticmethod
    def invitation_codes_to_response_list(codes: List[InvitationCode]) -> List[InvitationCodeResponse]:
        """Convert list of SQLAlchemy InvitationCodes to list of Pydantic InvitationCodeResponses."""
        return [SQLAlchemyAdapter.invitation_code_to_response(code) for code in codes]


class DatabaseValueExtractor:
    """Helper for safely extracting values from SQLAlchemy objects."""
    
    @staticmethod
    def safe_str(value: Any) -> str:
        """Safely extract string value."""
        if value is None:
            return ""
        return str(value)
    
    @staticmethod
    def safe_int(value: Any) -> int:
        """Safely extract integer value."""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def safe_float(value: Any) -> float:
        """Safely extract float value."""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def safe_bool(value: Any) -> bool:
        """Safely extract boolean value."""
        if value is None:
            return False
        return bool(value)
    
    @staticmethod
    def safe_datetime(value: Any) -> Optional[datetime]:
        """Safely extract datetime value."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return None


class TypeSafeAdapter:
    """Type-safe adapter using explicit value extraction."""
    
    @staticmethod
    def moderation_record_to_result_safe(record: Any) -> ModerationResult:
        """Type-safe conversion of ModerationRecord to ModerationResult."""
        return ModerationResult(
            moderation_id=DatabaseValueExtractor.safe_str(getattr(record, 'id', '')),
            content_hash=DatabaseValueExtractor.safe_str(getattr(record, 'content_hash', '')),
            ai_result=AIResult(
                inappropriate_probability=DatabaseValueExtractor.safe_int(getattr(record, 'inappropriate_probability', 0)),
                reason="AI analysis completed"
            ),
            final_decision=DatabaseValueExtractor.safe_str(getattr(record, 'final_decision', '')),
            reason="Decision based on AI analysis",
            created_at=DatabaseValueExtractor.safe_datetime(getattr(record, 'created_at', None)) or datetime.now(),
            word_count=DatabaseValueExtractor.safe_int(getattr(record, 'word_count', 0)),
            percentage_used=DatabaseValueExtractor.safe_float(getattr(record, 'percentage_used', 0.0))
        )
    
    @staticmethod
    def user_to_response_safe(user: Any) -> UserResponse:
        """Type-safe conversion of User to UserResponse."""
        return UserResponse(
            user_id=DatabaseValueExtractor.safe_str(getattr(user, 'user_id', '')),
            username=DatabaseValueExtractor.safe_str(getattr(user, 'username', '')),
            created_at=DatabaseValueExtractor.safe_datetime(getattr(user, 'created_at', None)) or datetime.now(),
            is_active=DatabaseValueExtractor.safe_bool(getattr(user, 'is_active', False))
        )
    
    @staticmethod
    def token_to_response_safe(token: Any, include_token: bool = False, token_value: Optional[str] = None) -> TokenResponse:
        """Type-safe conversion of APIToken to TokenResponse."""
        return TokenResponse(
            token_id=DatabaseValueExtractor.safe_str(getattr(token, 'token_id', '')),
            name=DatabaseValueExtractor.safe_str(getattr(token, 'name', '')),
            token=token_value if include_token else None,
            created_at=DatabaseValueExtractor.safe_datetime(getattr(token, 'created_at', None)) or datetime.now(),
            last_used=DatabaseValueExtractor.safe_datetime(getattr(token, 'last_used', None)),
            usage_count=DatabaseValueExtractor.safe_int(getattr(token, 'usage_count', 0)),
            is_active=DatabaseValueExtractor.safe_bool(getattr(token, 'is_active', False))
        )
    
    @staticmethod
    def invitation_code_to_response_safe(code: Any) -> InvitationCodeResponse:
        """Type-safe conversion of InvitationCode to InvitationCodeResponse."""
        max_uses_value = getattr(code, 'max_uses', None)
        return InvitationCodeResponse(
            code=DatabaseValueExtractor.safe_str(getattr(code, 'code', '')),
            created_at=DatabaseValueExtractor.safe_datetime(getattr(code, 'created_at', None)) or datetime.now(),
            expires_at=DatabaseValueExtractor.safe_datetime(getattr(code, 'expires_at', None)),
            max_uses=DatabaseValueExtractor.safe_int(max_uses_value) if max_uses_value is not None else None,
            current_uses=DatabaseValueExtractor.safe_int(getattr(code, 'current_uses', 0)),
            is_active=DatabaseValueExtractor.safe_bool(getattr(code, 'is_active', False))
        )


# Convenience functions for easy import
def convert_moderation_record(record: Any) -> ModerationResult:
    """Convert ModerationRecord to ModerationResult with type safety."""
    return TypeSafeAdapter.moderation_record_to_result_safe(record)


def convert_user(user: Any) -> UserResponse:
    """Convert User to UserResponse with type safety."""
    return TypeSafeAdapter.user_to_response_safe(user)


def convert_token(token: Any, include_token: bool = False, token_value: Optional[str] = None) -> TokenResponse:
    """Convert APIToken to TokenResponse with type safety."""
    return TypeSafeAdapter.token_to_response_safe(token, include_token, token_value)


def convert_invitation_code(code: Any) -> InvitationCodeResponse:
    """Convert InvitationCode to InvitationCodeResponse with type safety."""
    return TypeSafeAdapter.invitation_code_to_response_safe(code)


def convert_users_list(users: List[Any]) -> List[UserResponse]:
    """Convert list of Users to list of UserResponses with type safety."""
    return [convert_user(user) for user in users]


def convert_tokens_list(tokens: List[Any]) -> List[TokenResponse]:
    """Convert list of APITokens to list of TokenResponses with type safety."""
    return [convert_token(token) for token in tokens]


def convert_invitation_codes_list(codes: List[Any]) -> List[InvitationCodeResponse]:
    """Convert list of InvitationCodes to list of InvitationCodeResponses with type safety."""
    return [convert_invitation_code(code) for code in codes]
