"""
Background task processing using Celery for FIST Content Moderation System.

This module provides asynchronous task processing capabilities for:
- Large batch processing jobs
- Scheduled maintenance tasks
- Background data processing
- Long-running operations
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from celery import Celery
from celery.result import AsyncResult

from core.config import Config
from utils.batch_processor import batch_processor
from utils.cache import cache_manager
from utils.monitoring import metrics_collector

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'fist_tasks',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['background_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=Config.BATCH_TIMEOUT,
    task_soft_time_limit=Config.BATCH_TIMEOUT - 30,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,
    task_max_retries=3,
)


@celery_app.task(bind=True, name='process_batch_background')
def process_batch_background(
    self,
    job_id: str,
    contents: List[str],
    percentages: Optional[List[float]] = None,
    thresholds: Optional[List[int]] = None,
    probability_thresholds: Optional[Dict[str, int]] = None,
    user_id: Optional[str] = None
):
    """
    Process a batch of content moderation requests in the background.

    This task handles large batch processing jobs asynchronously,
    allowing the API to respond immediately while processing continues.
    """
    try:
        logger.info(f"Starting background batch processing for job {job_id}")

        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={
                'job_id': job_id,
                'current': 0,
                'total': len(contents),
                'status': 'Starting batch processing...'
            }
        )

        # Process the batch
        import asyncio
        result = asyncio.run(
            batch_processor.process_batch_async(
                job_id=job_id,
                contents=contents,
                percentages=percentages,
                thresholds=thresholds,
                probability_thresholds=probability_thresholds
            )
        )

        logger.info(f"Background batch processing completed for job {job_id}")

        return {
            'job_id': job_id,
            'status': 'completed',
            'result': result,
            'completed_at': datetime.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Background batch processing failed for job {job_id}: {exc}")

        # Update job status in batch processor
        if job_id in batch_processor.active_jobs:
            batch_processor.active_jobs[job_id]["status"] = "failed"
            batch_processor.active_jobs[job_id]["completed_at"] = datetime.now()
            batch_processor.active_jobs[job_id]["errors"].append({
                "error": f"Background task failed: {str(exc)}",
                "timestamp": datetime.now().isoformat()
            })

        self.update_state(
            state='FAILURE',
            meta={
                'job_id': job_id,
                'error': str(exc),
                'failed_at': datetime.now().isoformat()
            }
        )

        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(name='cleanup_old_jobs')
def cleanup_old_jobs():
    """
    Periodic task to clean up old completed jobs and cache entries.

    This task should be scheduled to run periodically (e.g., daily)
    to prevent memory leaks and maintain system performance.
    """
    try:
        logger.info("Starting periodic cleanup of old jobs and cache")

        # Clean up old batch jobs
        cleaned_jobs = batch_processor.cleanup_old_jobs(max_age_hours=24)

        # Clean up old cache entries (if needed)
        # Note: Redis handles TTL automatically, but we can force cleanup if needed
        cache_stats = cache_manager.get_cache_stats()

        # Clean up old Celery results (keep last 1000)
        # This would require additional implementation based on your needs

        result = {
            'cleaned_jobs': cleaned_jobs,
            'cache_stats': cache_stats,
            'cleanup_time': datetime.now().isoformat()
        }

        logger.info(f"Periodic cleanup completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Periodic cleanup failed: {exc}")
        raise


@celery_app.task(name='system_health_check')
def system_health_check():
    """
    Periodic system health check task.

    Monitors system health and can trigger alerts or corrective actions.
    """
    try:
        logger.info("Performing system health check")

        # Get comprehensive health status
        health_status = metrics_collector.health_check()

        # Get cache health
        cache_stats = cache_manager.get_cache_stats()

        # Get metrics summary
        metrics_summary = metrics_collector.get_metrics_summary()

        # Check for any critical issues
        critical_issues = []

        if health_status["status"] == "unhealthy":
            critical_issues.append("System health check failed")

        if not cache_manager.health_check():
            critical_issues.append("Cache system unhealthy")

        # Check error rate
        if metrics_summary.get("enabled") and metrics_summary.get("requests", {}).get("error_rate", 0) > 10:
            critical_issues.append(f"High error rate: {metrics_summary['requests']['error_rate']:.2f}%")

        result = {
            'timestamp': datetime.now().isoformat(),
            'health_status': health_status,
            'cache_stats': cache_stats,
            'metrics_summary': metrics_summary,
            'critical_issues': critical_issues,
            'overall_status': 'healthy' if not critical_issues else 'unhealthy'
        }

        if critical_issues:
            logger.warning(f"System health check found issues: {critical_issues}")
        else:
            logger.info("System health check passed")

        return result

    except Exception as exc:
        logger.error(f"System health check failed: {exc}")
        raise


@celery_app.task(name='generate_performance_report')
def generate_performance_report():
    """
    Generate comprehensive performance report.

    This task can be scheduled to run periodically to generate
    performance reports for monitoring and optimization.
    """
    try:
        logger.info("Generating performance report")

        # Get comprehensive metrics
        metrics_summary = metrics_collector.get_metrics_summary()
        cache_stats = cache_manager.get_cache_stats()
        batch_summary = batch_processor.get_active_jobs_summary()

        # Calculate additional insights
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'period': '24h',  # Could be configurable
            'metrics': metrics_summary,
            'cache_performance': cache_stats,
            'batch_processing': batch_summary,
            'recommendations': []
        }

        # Add performance recommendations
        if metrics_summary.get("enabled"):
            cache_hit_rate = metrics_summary.get("cache", {}).get("hit_rate", 0)
            if cache_hit_rate < 50:
                report['recommendations'].append(
                    f"Low cache hit rate ({cache_hit_rate:.1f}%). Consider increasing cache TTL or reviewing content patterns."
                )

            error_rate = metrics_summary.get("requests", {}).get("error_rate", 0)
            if error_rate > 5:
                report['recommendations'].append(
                    f"High error rate ({error_rate:.1f}%). Review error logs and system health."
                )

            avg_response_time = metrics_summary.get("performance", {}).get("avg_response_time_ms", 0)
            if avg_response_time > 2000:
                report['recommendations'].append(
                    f"High average response time ({avg_response_time:.0f}ms). Consider optimization or scaling."
                )

        logger.info("Performance report generated successfully")
        return report

    except Exception as exc:
        logger.error(f"Performance report generation failed: {exc}")
        raise


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'cleanup_old_jobs',
        'schedule': 3600.0,  # Run every hour
    },
    'system-health-check': {
        'task': 'system_health_check',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'performance-report': {
        'task': 'generate_performance_report',
        'schedule': 86400.0,  # Run daily
    },
}


class BackgroundTaskManager:
    """Manager for background tasks and job tracking."""

    def __init__(self):
        """Initialize background task manager."""
        self.celery_app = celery_app

    def submit_batch_job(
        self,
        job_id: str,
        contents: List[str],
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Submit a batch processing job to background queue."""
        try:
            task = process_batch_background.delay(
                job_id=job_id,
                contents=contents,
                percentages=percentages,
                thresholds=thresholds,
                probability_thresholds=probability_thresholds,
                user_id=user_id
            )

            logger.info(f"Submitted batch job {job_id} to background queue with task ID {task.id}")
            return task.id

        except Exception as e:
            logger.error(f"Failed to submit batch job {job_id} to background queue: {e}")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a background task."""
        try:
            result = AsyncResult(task_id, app=celery_app)

            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'info': result.info,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None
            }

        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a background task."""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False

    def get_worker_stats(self) -> Dict[str, Any]:
        """Get Celery worker statistics."""
        try:
            inspect = celery_app.control.inspect()

            return {
                'active_tasks': inspect.active(),
                'scheduled_tasks': inspect.scheduled(),
                'reserved_tasks': inspect.reserved(),
                'worker_stats': inspect.stats()
            }
        except Exception as e:
            logger.error(f"Error getting worker stats: {e}")
            return {'error': str(e)}


# Global background task manager instance
background_task_manager = BackgroundTaskManager()
