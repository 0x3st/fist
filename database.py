"""
Database operations and setup for FIST Content Moderation System.

This module handles all database-related functionality including
session management, table creation, and CRUD operations.
Privacy-focused: uses hash storage for sensitive data.
"""
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import Config
from models import Base, ModerationRecord, ConfigRecord, User, APIToken, InvitationCode, Admin


# Database Setup
engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_config_from_database():
    """Load configuration from database and update Config class."""
    import ast
    import json

    db = SessionLocal()
    try:
        # Load max_users from database
        max_users_str = DatabaseOperations.get_config_value(db, "max_users")
        if max_users_str:
            Config.MAX_USERS = int(max_users_str)

        # Load percentages from database
        percentages_str = DatabaseOperations.get_config_value(db, "percentages")
        if percentages_str:
            Config.DEFAULT_PERCENTAGES = ast.literal_eval(percentages_str)

        # Load thresholds from database
        thresholds_str = DatabaseOperations.get_config_value(db, "thresholds")
        if thresholds_str:
            Config.DEFAULT_THRESHOLDS = ast.literal_eval(thresholds_str)

        # Load probability thresholds from database
        prob_thresholds_str = DatabaseOperations.get_config_value(db, "probability_thresholds")
        if prob_thresholds_str:
            Config.DEFAULT_PROBABILITY_THRESHOLDS = json.loads(prob_thresholds_str)

        # Load AI model from database
        ai_model_str = DatabaseOperations.get_config_value(db, "ai_model")
        if ai_model_str:
            Config.AI_MODEL = ai_model_str

        # Load AI base URL from database
        ai_base_url_str = DatabaseOperations.get_config_value(db, "ai_base_url")
        if ai_base_url_str:
            Config.AI_BASE_URL = ai_base_url_str

        # Load AI API key from database
        ai_api_key_str = DatabaseOperations.get_config_value(db, "ai_api_key")
        if ai_api_key_str:
            Config.AI_API_KEY = ai_api_key_str

    except Exception as e:
        print(f"Warning: Failed to load configuration from database: {e}")
    finally:
        db.close()


class DatabaseOperations:
    """Database operations for moderation records."""

    @staticmethod
    def create_moderation_record(
        db: Session,
        original_content: str,
        word_count: int,
        percentage_used: float,
        inappropriate_probability: int,
        final_decision: str
    ) -> ModerationRecord:
        """Create a new moderation record - privacy focused."""
        # Create SHA-256 hash of content for verification
        content_hash = hashlib.sha256(original_content.encode('utf-8')).hexdigest()

        record = ModerationRecord(
            content_hash=content_hash,
            word_count=word_count,
            percentage_used=percentage_used,
            inappropriate_probability=inappropriate_probability,
            final_decision=final_decision
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_moderation_record(db: Session, moderation_id: str) -> Optional[ModerationRecord]:
        """Get a moderation record by ID."""
        return db.query(ModerationRecord).filter(ModerationRecord.id == moderation_id).first()

    # Statistics and records listing removed for privacy protection

    @staticmethod
    def get_config_value(db: Session, config_key: str) -> Optional[str]:
        """Get a configuration value by key."""
        config = db.query(ConfigRecord).filter(ConfigRecord.config_key == config_key).first()
        return config.config_value if config else None  # type: ignore

    @staticmethod
    def set_config_value(db: Session, config_key: str, config_value: str, updated_by: str) -> ConfigRecord:
        """Set or update a configuration value."""
        existing = db.query(ConfigRecord).filter(ConfigRecord.config_key == config_key).first()
        if existing:
            existing.config_value = config_value  # type: ignore
            existing.updated_by = updated_by  # type: ignore
            existing.updated_at = datetime.now()  # type: ignore
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_config = ConfigRecord(
                config_key=config_key,
                config_value=config_value,
                updated_by=updated_by
            )
            db.add(new_config)
            db.commit()
            db.refresh(new_config)
            return new_config

    # User Management Operations
    @staticmethod
    def create_user(db: Session, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(
            username=username,
            password_hash=password_hash
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def is_user_active(user: User) -> bool:
        """Check if user is active."""
        return bool(user.is_active)

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_all_users(db: Session, limit: int = 100) -> List[User]:
        """Get all users."""
        return db.query(User).limit(limit).all()

    @staticmethod
    def get_user_count(db: Session) -> int:
        """Get total number of users."""
        return db.query(User).count()

    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> bool:
        """Deactivate a user."""
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.is_active = False  # type: ignore
            db.commit()
            return True
        return False

    @staticmethod
    def update_user_password(db: Session, user_id: str, new_password_hash: str) -> bool:
        """Update user password."""
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.password_hash = new_password_hash  # type: ignore
            db.commit()
            return True
        return False

    # API Token Operations
    @staticmethod
    def create_api_token(db: Session, user_id: str, name: str, token_hash: str) -> APIToken:
        """Create a new API token."""
        token = APIToken(
            user_id=user_id,
            name=name,
            token_hash=token_hash
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_user_tokens(db: Session, user_id: str) -> List[APIToken]:
        """Get all tokens for a user."""
        return db.query(APIToken).filter(APIToken.user_id == user_id, APIToken.is_active == True).all()

    @staticmethod
    def get_token_by_hash(db: Session, token_hash: str) -> Optional[APIToken]:
        """Get token by hash."""
        return db.query(APIToken).filter(APIToken.token_hash == token_hash, APIToken.is_active == True).first()

    @staticmethod
    def update_token_last_used(db: Session, token_id: str) -> None:
        """Update token last used timestamp and increment usage count."""
        token = db.query(APIToken).filter(APIToken.token_id == token_id).first()
        if token:
            token.last_used = datetime.now()  # type: ignore
            token.usage_count = (token.usage_count or 0) + 1  # type: ignore
            db.commit()

    @staticmethod
    def deactivate_token(db: Session, token_id: str, user_id: str) -> bool:
        """Deactivate a token."""
        token = db.query(APIToken).filter(
            APIToken.token_id == token_id,
            APIToken.user_id == user_id
        ).first()
        if token:
            token.is_active = False  # type: ignore
            db.commit()
            return True
        return False

    # Invitation Code Operations
    @staticmethod
    def create_invitation_code(
        db: Session,
        code: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
        max_uses: Optional[int] = None
    ) -> InvitationCode:
        """Create a new invitation code."""
        invitation = InvitationCode(
            code=code,
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def get_invitation_code(db: Session, code: str) -> Optional[InvitationCode]:
        """Get invitation code by code."""
        return db.query(InvitationCode).filter(InvitationCode.code == code).first()

    @staticmethod
    def is_invitation_active(invitation: InvitationCode) -> bool:
        """Check if invitation code is active."""
        return bool(invitation.is_active)

    @staticmethod
    def is_invitation_expired(invitation: InvitationCode) -> bool:
        """Check if invitation code is expired."""
        expires_at = getattr(invitation, 'expires_at', None)
        if expires_at is None:
            return False
        return expires_at < datetime.now()

    @staticmethod
    def is_invitation_max_uses_reached(invitation: InvitationCode) -> bool:
        """Check if invitation code has reached max uses."""
        max_uses = getattr(invitation, 'max_uses', None)
        current_uses = getattr(invitation, 'current_uses', 0)
        if max_uses is None:
            return False
        return current_uses >= max_uses

    @staticmethod
    def validate_invitation_code(db: Session, code: str) -> Tuple[bool, str]:
        """Validate an invitation code and return (is_valid, error_message)."""
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()

        if not invitation:
            return False, "Invalid invitation code"

        if not DatabaseOperations.is_invitation_active(invitation):
            return False, "Invitation code is inactive"

        if DatabaseOperations.is_invitation_expired(invitation):
            return False, "Invitation code has expired"

        if DatabaseOperations.is_invitation_max_uses_reached(invitation):
            return False, "Invitation code has reached maximum uses"

        return True, ""

    @staticmethod
    def use_invitation_code(db: Session, code: str) -> bool:
        """Use an invitation code (increment usage count)."""
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()
        if not invitation:
            return False

        # Validate the code first
        is_valid, _ = DatabaseOperations.validate_invitation_code(db, code)
        if not is_valid:
            return False

        # Increment usage count
        invitation.current_uses += 1  # type: ignore
        db.commit()
        return True

    @staticmethod
    def get_all_invitation_codes(db: Session) -> List[InvitationCode]:
        """Get all invitation codes."""
        return db.query(InvitationCode).all()

    @staticmethod
    def deactivate_invitation_code(db: Session, code: str) -> bool:
        """Deactivate an invitation code."""
        invitation = db.query(InvitationCode).filter(InvitationCode.code == code).first()
        if invitation:
            invitation.is_active = False  # type: ignore
            db.commit()
            return True
        return False

    # Usage Statistics - privacy focused
    @staticmethod
    def get_user_usage_stats(db: Session, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user - privacy focused."""
        from sqlalchemy import and_

        # Only show active tokens count - no historical data
        tokens_count = db.query(APIToken).filter(
            and_(
                APIToken.user_id == user_id,
                APIToken.is_active == True
            )
        ).count()

        return {
            "tokens_count": tokens_count
        }

    # Admin Management Operations
    @staticmethod
    def create_admin(db: Session, username: str, password_hash: str) -> Admin:
        """Create a new admin."""
        admin = Admin(
            username=username,
            password_hash=password_hash
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
        """Get admin by username."""
        return db.query(Admin).filter(Admin.username == username, Admin.is_active == True).first()

    @staticmethod
    def get_admin_by_id(db: Session, admin_id: str) -> Optional[Admin]:
        """Get admin by ID."""
        return db.query(Admin).filter(Admin.admin_id == admin_id, Admin.is_active == True).first()

    @staticmethod
    def update_admin_password(db: Session, username: str, new_password_hash: str) -> bool:
        """Update admin password."""
        admin = db.query(Admin).filter(Admin.username == username, Admin.is_active == True).first()
        if admin:
            admin.password_hash = new_password_hash  # type: ignore
            admin.updated_at = datetime.now()  # type: ignore
            db.commit()
            return True
        return False

    @staticmethod
    def admin_exists(db: Session) -> bool:
        """Check if any admin exists in the database."""
        return db.query(Admin).filter(Admin.is_active == True).count() > 0

    # User moderation history removed for privacy protection
