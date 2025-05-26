"""
FIST Content Moderation System - Production API

This is the main file for the FIST system providing a FastAPI-based content moderation service.

The system contains:
- FastAPI web server with REST endpoints
- AI model integration for content assessment
- SQLite database for storing moderation results
- Intelligent content piercing based on length
- Configurable decision thresholds

Architecture:
- AI component returns only probability scores (0-100%) with brief reasons
- analyze_result() function handles final decision-making logic based on configurable thresholds
- Clear separation between AI assessment and business logic decisions
- Simplified risk levels: LOW (≤20%) → APPROVED, MEDIUM (21-80%) → MANUAL_REVIEW, HIGH (>80%) → REJECTED
"""
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, Request, Form, Cookie
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from jose import JWTError, jwt

from ai_connector import AIConnector

# Configuration
class Config:
    """Configuration class for FIST system."""
    DATABASE_URL = "sqlite:///./fist.db"
    AI_API_KEY = os.getenv("AI_API_KEY", "sk-488d88049a9440a591bb948fa8fea5ca")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
    DEFAULT_PERCENTAGES: List[float] = [0.8, 0.6, 0.4, 0.2]
    DEFAULT_THRESHOLDS: List[int] = [500, 1000, 3000]
    DEFAULT_PROBABILITY_THRESHOLDS: Dict[str, int] = {"low": 20, "high": 80}
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Admin Authentication
    SECRET_KEY = os.getenv("SECRET_KEY", "fist-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in production!

# Authentication setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

# Pydantic Models
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
    """Final moderation result model."""
    moderation_id: str = Field(..., description="Unique identifier for this moderation")
    original_content: str = Field(..., description="Original content submitted")
    pierced_content: str = Field(..., description="Content portion that was analyzed")
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

class StatsResponse(BaseModel):
    """Statistics response model."""
    total_moderations: int = Field(..., description="Total number of moderations performed")
    approved_count: int = Field(..., description="Number of approved content")
    rejected_count: int = Field(..., description="Number of rejected content")
    manual_review_count: int = Field(..., description="Number of content requiring manual review")
    average_probability: float = Field(..., description="Average inappropriateness probability")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(..., description="Error timestamp")

# Database Setup
engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ModerationRecord(Base):
    """Database model for moderation records."""
    __tablename__ = "moderation_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_content = Column(Text, nullable=False)
    pierced_content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    percentage_used = Column(Float, nullable=False)
    inappropriate_probability = Column(Integer, nullable=False)
    ai_reason = Column(Text, nullable=False)
    final_decision = Column(String(1), nullable=False)  # A, R, M
    final_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class ConfigRecord(Base):
    """Database model for system configuration."""
    __tablename__ = "config_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String(100), nullable=False)

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

# Moderation Service
class ModerationService:
    """Service class for content moderation."""

    def __init__(self):
        """Initialize the moderation service."""
        self.ai_connector = AIConnector(Config.AI_API_KEY, Config.AI_BASE_URL)
        self.ai_connector.set_model(Config.AI_MODEL)

    def pierce_content(self, text: str, percentages: Optional[List[float]] = None, thresholds: Optional[List[int]] = None) -> tuple[str, float]:
        """Pierce content into pieces according to the rules."""
        words = text.split()
        if len(words) == 1 and len(text.strip()) > 10:
            words = list(text.strip())

        word_count = len(words)
        if percentages is None:
            percentages = Config.DEFAULT_PERCENTAGES
        if thresholds is None:
            thresholds = Config.DEFAULT_THRESHOLDS

        percentage_index = 0
        for i, threshold in enumerate(thresholds):
            if word_count < threshold:
                break
            percentage_index = i + 1

        if percentage_index < len(percentages):
            percentage = percentages[percentage_index]
        else:
            percentage = percentages[-1]

        words_to_keep = int(word_count * percentage)
        if word_count > words_to_keep:
            max_start_index = word_count - words_to_keep
            start_index = random.randint(0, max_start_index)
        else:
            start_index = 0

        selected_words = words[start_index:start_index + words_to_keep]
        if len(words) > 1 and all(len(word) == 1 for word in words[:10]):
            pierced_content = ''.join(selected_words)
        else:
            pierced_content = ' '.join(selected_words)

        return pierced_content, percentage

    def check_content_with_ai(self, text: str) -> Dict[str, Any]:
        """Check content with AI."""
        return self.ai_connector.moderate_content(text)

    def analyze_result(self, ai_result: Dict[str, Any], probability_thresholds: Optional[Dict[str, int]] = None) -> Dict[str, str]:
        """Analyze the AI moderation result and make the final decision."""
        if probability_thresholds is None:
            probability_thresholds = Config.DEFAULT_PROBABILITY_THRESHOLDS

        inappropriate_prob = ai_result.get("inappropriate_probability", 50)
        ai_reason = ai_result.get("reason", "No reason provided")

        if inappropriate_prob <= probability_thresholds["low"]:
            final_decision = "A"
            reason = f"Low risk ({inappropriate_prob}%): {ai_reason}"
        elif inappropriate_prob <= probability_thresholds["high"]:
            final_decision = "M"
            reason = f"Medium risk ({inappropriate_prob}%): {ai_reason}"
        else:
            final_decision = "R"
            reason = f"High risk ({inappropriate_prob}%): {ai_reason}"

        return {"final_decision": final_decision, "reason": reason}

    def moderate_content(self, content: str, percentages: Optional[List[float]] = None, thresholds: Optional[List[int]] = None, probability_thresholds: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Perform complete content moderation."""
        words = content.split()
        if len(words) == 1 and len(content.strip()) > 10:
            words = list(content.strip())
        word_count = len(words)

        pierced_content, percentage_used = self.pierce_content(content, percentages, thresholds)
        ai_result = self.check_content_with_ai(pierced_content)
        analysis = self.analyze_result(ai_result, probability_thresholds)

        return {
            "original_content": content,
            "pierced_content": pierced_content,
            "word_count": word_count,
            "percentage_used": percentage_used,
            "ai_result": ai_result,
            "final_decision": analysis["final_decision"],
            "reason": analysis["reason"]
        }

# Database Operations
class DatabaseOperations:
    """Database operations for moderation records."""

    @staticmethod
    def create_moderation_record(db: Session, original_content: str, pierced_content: str, word_count: int, percentage_used: float, inappropriate_probability: int, ai_reason: str, final_decision: str, final_reason: str) -> ModerationRecord:
        """Create a new moderation record."""
        record = ModerationRecord(
            original_content=original_content,
            pierced_content=pierced_content,
            word_count=word_count,
            percentage_used=percentage_used,
            inappropriate_probability=inappropriate_probability,
            ai_reason=ai_reason,
            final_decision=final_decision,
            final_reason=final_reason
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_moderation_record(db: Session, moderation_id: str) -> Optional[ModerationRecord]:
        """Get a moderation record by ID."""
        return db.query(ModerationRecord).filter(ModerationRecord.id == moderation_id).first()

    @staticmethod
    def get_all_moderation_records(db: Session, limit: int = 100) -> List[ModerationRecord]:
        """Get all moderation records with limit."""
        return db.query(ModerationRecord).order_by(ModerationRecord.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_stats(db: Session) -> dict:
        """Get moderation statistics."""
        total = db.query(ModerationRecord).count()
        approved = db.query(ModerationRecord).filter(ModerationRecord.final_decision == "A").count()
        rejected = db.query(ModerationRecord).filter(ModerationRecord.final_decision == "R").count()
        manual_review = db.query(ModerationRecord).filter(ModerationRecord.final_decision == "M").count()

        avg_prob_result = db.query(ModerationRecord.inappropriate_probability).all()
        avg_probability = sum(row[0] for row in avg_prob_result) / len(avg_prob_result) if avg_prob_result else 0.0

        return {
            "total_moderations": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "manual_review_count": manual_review,
            "average_probability": round(avg_probability, 2)
        }

# Create FastAPI app
app = FastAPI(
    title="FIST Content Moderation API",
    description="Fast, Intuitive and Sensitive Test - Content Moderation System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize moderation service
moderation_service = ModerationService()

# Authentication dependency
def get_current_user(token: str = Cookie(None)):
    """Get current authenticated user from cookie."""
    if not token:
        return None
    username = verify_token(token)
    if username != Config.ADMIN_USERNAME:
        return None
    return username

def require_auth(token: str = Cookie(None)):
    """Require authentication for admin endpoints."""
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0"
    )

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_content(
    request: ModerationRequest,
    db: Session = Depends(get_db)
):
    """
    Moderate content using the FIST system.

    This endpoint:
    1. Pierces the content based on word count
    2. Analyzes it with AI
    3. Makes a final decision (Approved/Rejected/Manual Review)
    4. Stores the result in the database
    """
    try:
        # Perform moderation
        result = moderation_service.moderate_content(
            content=request.content,
            percentages=request.percentages,
            thresholds=request.thresholds,
            probability_thresholds=request.probability_thresholds
        )

        # Store in database
        record = DatabaseOperations.create_moderation_record(
            db=db,
            original_content=result["original_content"],
            pierced_content=result["pierced_content"],
            word_count=result["word_count"],
            percentage_used=result["percentage_used"],
            inappropriate_probability=result["ai_result"]["inappropriate_probability"],
            ai_reason=result["ai_result"]["reason"],
            final_decision=result["final_decision"],
            final_reason=result["reason"]
        )

        # Prepare response
        moderation_result = ModerationResult(
            moderation_id=record.id,
            original_content=result["original_content"],
            pierced_content=result["pierced_content"],
            ai_result=AIResult(
                inappropriate_probability=result["ai_result"]["inappropriate_probability"],
                reason=result["ai_result"]["reason"]
            ),
            final_decision=result["final_decision"],
            reason=result["reason"],
            created_at=record.created_at,
            word_count=result["word_count"],
            percentage_used=result["percentage_used"]
        )

        return ModerationResponse(
            moderation_id=record.id,
            status="completed",
            result=moderation_result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Moderation failed: {str(e)}"
        )

@app.get("/results/{moderation_id}", response_model=ModerationResult)
async def get_moderation_result(
    moderation_id: str,
    db: Session = Depends(get_db)
):
    """Get moderation result by ID."""
    record = DatabaseOperations.get_moderation_record(db, moderation_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found"
        )

    return ModerationResult(
        moderation_id=record.id,
        original_content=record.original_content,
        pierced_content=record.pierced_content,
        ai_result=AIResult(
            inappropriate_probability=record.inappropriate_probability,
            reason=record.ai_reason
        ),
        final_decision=record.final_decision,
        reason=record.final_reason,
        created_at=record.created_at,
        word_count=record.word_count,
        percentage_used=record.percentage_used
    )

@app.get("/admin/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get moderation statistics."""
    stats = DatabaseOperations.get_stats(db)
    return StatsResponse(**stats)

@app.get("/admin/records", response_model=List[ModerationResult])
async def get_all_records(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all moderation records (admin endpoint)."""
    records = DatabaseOperations.get_all_moderation_records(db, limit)

    return [
        ModerationResult(
            moderation_id=record.id,
            original_content=record.original_content,
            pierced_content=record.pierced_content,
            ai_result=AIResult(
                inappropriate_probability=record.inappropriate_probability,
                reason=record.ai_reason
            ),
            final_decision=record.final_decision,
            reason=record.final_reason,
            created_at=record.created_at,
            word_count=record.word_count,
            percentage_used=record.percentage_used
        )
        for record in records
    ]

# Admin Web Interface Endpoints

@app.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request, user: Optional[str] = Depends(get_current_user)):
    """Admin login page or redirect to dashboard if already logged in."""
    if user:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin/login")
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

@app.get("/admin/logout")
async def admin_logout():
    """Handle admin logout."""
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("token")
    return response

@app.get("/admin/dashboard", response_class=HTMLResponse)
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

@app.get("/admin/config", response_class=HTMLResponse)
async def admin_config_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin configuration page."""
    # Get current configuration
    current_config = {
        "percentages": Config.DEFAULT_PERCENTAGES,
        "thresholds": Config.DEFAULT_THRESHOLDS,
        "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
        "ai_model": Config.AI_MODEL
    }

    return templates.TemplateResponse("config.html", {
        "request": request,
        "user": user,
        "config": current_config
    })

@app.post("/admin/config")
async def admin_update_config(
    request: Request,
    user: str = Depends(require_auth),
    db: Session = Depends(get_db),
    percentages: str = Form(...),
    thresholds: str = Form(...),
    low_threshold: int = Form(...),
    high_threshold: int = Form(...),
    ai_model: str = Form(...)
):
    """Handle configuration updates."""
    try:
        # Parse and validate percentages
        new_percentages = [float(x.strip()) for x in percentages.split(",")]
        new_thresholds = [int(x.strip()) for x in thresholds.split(",")]

        # Validate ranges
        if not all(0 <= p <= 1 for p in new_percentages):
            raise ValueError("Percentages must be between 0 and 1")
        if not all(t > 0 for t in new_thresholds):
            raise ValueError("Thresholds must be positive")
        if not (0 <= low_threshold <= 100 and 0 <= high_threshold <= 100):
            raise ValueError("Probability thresholds must be between 0 and 100")
        if low_threshold >= high_threshold:
            raise ValueError("Low threshold must be less than high threshold")

        # Update configuration in database
        config_updates = [
            ("percentages", str(new_percentages)),
            ("thresholds", str(new_thresholds)),
            ("probability_thresholds", f'{{"low": {low_threshold}, "high": {high_threshold}}}'),
            ("ai_model", ai_model)
        ]

        for key, value in config_updates:
            existing = db.query(ConfigRecord).filter(ConfigRecord.config_key == key).first()
            if existing:
                existing.config_value = value
                existing.updated_by = user
                existing.updated_at = datetime.now()
            else:
                new_config = ConfigRecord(
                    config_key=key,
                    config_value=value,
                    updated_by=user
                )
                db.add(new_config)

        db.commit()

        # Update runtime configuration
        Config.DEFAULT_PERCENTAGES = new_percentages
        Config.DEFAULT_THRESHOLDS = new_thresholds
        Config.DEFAULT_PROBABILITY_THRESHOLDS = {"low": low_threshold, "high": high_threshold}
        Config.AI_MODEL = ai_model

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
                "ai_model": ai_model
            },
            "success": "Configuration updated successfully!"
        })

    except Exception as e:
        return templates.TemplateResponse("config.html", {
            "request": request,
            "user": user,
            "config": {
                "percentages": Config.DEFAULT_PERCENTAGES,
                "thresholds": Config.DEFAULT_THRESHOLDS,
                "probability_thresholds": Config.DEFAULT_PROBABILITY_THRESHOLDS,
                "ai_model": Config.AI_MODEL
            },
            "error": f"Configuration update failed: {str(e)}"
        })

@app.get("/admin/records", response_class=HTMLResponse)
async def admin_records_page(request: Request, user: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Admin records page."""
    records = DatabaseOperations.get_all_moderation_records(db, limit=100)

    return templates.TemplateResponse("records.html", {
        "request": request,
        "user": user,
        "records": records
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG
    )
