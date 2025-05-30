"""
FIST Content Moderation System - Production API

This is the main application file for the FIST system providing a FastAPI-based content moderation service.

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
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from config import Config
from models import ErrorResponse
from database import create_tables
from api_routes import router as api_router
from admin_routes import router as admin_router

# Lifespan event handler
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    create_tables()
    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(
    title="FIST Content Moderation API",
    description="Fast, Intuitive and Sensitive Test - Content Moderation System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump()
    )


# Include routers
app.include_router(api_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG
    )
