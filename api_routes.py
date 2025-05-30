"""
API routes for FIST Content Moderation System.

This module contains all REST API endpoints for content moderation,
health checks, and statistics.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session

from models import (
    ModerationRequest, ModerationResponse, ModerationResult, AIResult,
    HealthResponse
)
from database import get_db, DatabaseOperations
from services import ModerationService
from auth import require_api_auth

# Create API router
router = APIRouter(prefix="/api")

# Initialize moderation service
moderation_service = ModerationService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0"
    )


async def get_authenticated_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """Get authenticated user from API token."""
    # Create a new dependency that properly injects the database
    return require_api_auth(authorization, db)


@router.post("/moderate", response_model=ModerationResponse)
async def moderate_content(
    request: ModerationRequest,
    user_id: str = Depends(get_authenticated_user),
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

        # Store in database (privacy focused - only hash and metadata)
        record = DatabaseOperations.create_moderation_record(
            db=db,
            original_content=result["original_content"],
            word_count=result["word_count"],
            percentage_used=result["percentage_used"],
            inappropriate_probability=result["ai_result"]["inappropriate_probability"],
            final_decision=result["final_decision"]
        )

        # Prepare response (return actual content to user, but don't store it)
        moderation_result = ModerationResult(
            moderation_id=record.id,  # type: ignore
            content_hash=record.content_hash,  # type: ignore
            ai_result=AIResult(
                inappropriate_probability=result["ai_result"]["inappropriate_probability"],
                reason=result["ai_result"]["reason"]
            ),
            final_decision=result["final_decision"],
            reason=result["reason"],
            created_at=record.created_at,  # type: ignore
            word_count=result["word_count"],
            percentage_used=result["percentage_used"]
        )

        return ModerationResponse(
            moderation_id=record.id,  # type: ignore
            status="completed",
            result=moderation_result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Moderation failed: {str(e)}"
        )


@router.get("/results/{moderation_id}", response_model=ModerationResult)
async def get_moderation_result(
    moderation_id: str,
    db: Session = Depends(get_db)
):
    """Get moderation result by ID - privacy focused."""
    record = DatabaseOperations.get_moderation_record(db, moderation_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation record not found"
        )

    return ModerationResult(
        moderation_id=record.id,  # type: ignore
        content_hash=record.content_hash,  # type: ignore
        ai_result=AIResult(
            inappropriate_probability=record.inappropriate_probability,  # type: ignore
            reason="AI analysis completed"  # Generic reason for privacy
        ),
        final_decision=record.final_decision,  # type: ignore
        reason="Decision based on AI analysis",  # Generic reason for privacy
        created_at=record.created_at,  # type: ignore
        word_count=record.word_count,  # type: ignore
        percentage_used=record.percentage_used  # type: ignore
    )


# Admin endpoints removed for privacy protection
