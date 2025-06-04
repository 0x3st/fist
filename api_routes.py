"""
API routes for FIST Content Moderation System.

This module contains all REST API endpoints for content moderation.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session

from models import (
    ModerationRequest, ModerationResponse, ModerationResult, AIResult,
    BatchModerationRequest, BatchModerationResponse, BatchJobStatusResponse,
    HealthCheckResponse, MetricsResponse, CacheStatsResponse
)
from database import get_db, DatabaseOperations
from services import ModerationService
from auth import require_api_auth
from batch_processor import batch_processor
from background_tasks import background_task_manager
from monitoring import metrics_collector, monitor_endpoint
from cache import cache_manager

# Create API router
router = APIRouter(prefix="/api")

# Initialize moderation service
moderation_service = ModerationService()


async def get_authenticated_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """Get authenticated user from API token."""
    return require_api_auth(authorization, db)


@router.post("/moderate", response_model=ModerationResponse)
@monitor_endpoint("/api/moderate")
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

        # Prepare response
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


@router.post("/moderate/batch", response_model=BatchModerationResponse)
@monitor_endpoint("/api/moderate/batch")
async def moderate_content_batch(
    request: BatchModerationRequest,
    user_id: str = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Process multiple content items for moderation in batch.

    This endpoint supports both synchronous and asynchronous processing:
    - For small batches (background=False): Process immediately and return results
    - For large batches (background=True): Queue for background processing
    """
    try:
        # Create batch job
        job_id = batch_processor.create_batch_job(
            contents=request.contents,
            percentages=request.percentages,
            thresholds=request.thresholds,
            probability_thresholds=request.probability_thresholds,
            user_id=user_id
        )

        if request.background:
            # Submit to background queue
            task_id = background_task_manager.submit_batch_job(
                job_id=job_id,
                contents=request.contents,
                percentages=request.percentages,
                thresholds=request.thresholds,
                probability_thresholds=request.probability_thresholds,
                user_id=user_id
            )

            job_info = batch_processor.get_job_status(job_id)
            return BatchModerationResponse(
                job_id=job_id,
                status="queued",
                total_items=len(request.contents),
                processed_items=0,
                progress_percent=0.0,
                created_at=job_info["created_at"],
                background_task_id=task_id
            )
        else:
            # Process synchronously
            result = await batch_processor.process_batch_async(
                job_id=job_id,
                contents=request.contents,
                percentages=request.percentages,
                thresholds=request.thresholds,
                probability_thresholds=request.probability_thresholds
            )

            job_info = batch_processor.get_job_status(job_id)
            return BatchModerationResponse(
                job_id=job_id,
                status=result["status"],
                total_items=result["total_items"],
                processed_items=result["successful_items"],
                progress_percent=100.0,
                results=[ModerationResult(**r) for r in result["results"]],
                errors=result["errors"],
                created_at=job_info["created_at"],
                started_at=job_info["started_at"],
                completed_at=job_info["completed_at"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch moderation failed: {str(e)}"
        )


@router.get("/moderate/batch/{job_id}/status", response_model=BatchJobStatusResponse)
async def get_batch_job_status(
    job_id: str,
    user_id: str = Depends(get_authenticated_user)
):
    """Get status of a batch moderation job."""
    job_info = batch_processor.get_job_status(job_id)

    if not job_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    # Check if user owns this job (basic security)
    if job_info.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this batch job"
        )

    return BatchJobStatusResponse(
        job_id=job_id,
        status=job_info["status"],
        total_items=job_info["total_items"],
        processed_items=job_info["processed_items"],
        progress_percent=job_info["progress_percent"],
        elapsed_time_seconds=job_info.get("elapsed_time_seconds"),
        estimated_remaining_seconds=job_info.get("estimated_remaining_seconds"),
        errors_count=len(job_info.get("errors", []))
    )


@router.get("/moderate/batch/{job_id}/results")
async def get_batch_job_results(
    job_id: str,
    user_id: str = Depends(get_authenticated_user)
):
    """Get results of a completed batch moderation job."""
    results = batch_processor.get_job_results(job_id)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    # Check if user owns this job (basic security)
    job_info = batch_processor.get_job_status(job_id)
    if job_info and job_info.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this batch job"
        )

    return results


# Monitoring and Health Check Endpoints
@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive system health check."""
    health_status = metrics_collector.health_check()
    return HealthCheckResponse(**health_status)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system performance metrics."""
    metrics = metrics_collector.get_metrics_summary()
    return MetricsResponse(**metrics)


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus-formatted metrics."""
    from fastapi.responses import PlainTextResponse
    metrics_data = metrics_collector.get_prometheus_metrics()
    return PlainTextResponse(content=metrics_data, media_type="text/plain")


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache performance statistics."""
    stats = cache_manager.get_cache_stats()
    return CacheStatsResponse(**stats)


@router.delete("/cache/clear")
async def clear_cache(
    user_id: str = Depends(get_authenticated_user)
):
    """Clear cache entries (requires authentication)."""
    try:
        cleared_count = cache_manager.clear_cache()
        return {
            "message": f"Cache cleared successfully",
            "cleared_entries": cleared_count,
            "cleared_by": user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
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
            reason="AI analysis completed"
        ),
        final_decision=record.final_decision,  # type: ignore
        reason="Decision based on AI analysis",
        created_at=record.created_at,  # type: ignore
        word_count=record.word_count,  # type: ignore
        percentage_used=record.percentage_used  # type: ignore
    )
