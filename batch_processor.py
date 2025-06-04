"""
Batch processing system for FIST Content Moderation System.

This module provides efficient batch processing capabilities for handling
multiple content moderation requests simultaneously with parallel processing
and progress tracking.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from services import ModerationService
from cache import cache_manager
from monitoring import metrics_collector
from config import Config

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles batch processing of content moderation requests."""
    
    def __init__(self):
        """Initialize batch processor."""
        self.moderation_service = ModerationService()
        self.active_jobs = {}  # Store active batch jobs
        self.max_workers = min(32, (Config.MAX_BATCH_SIZE // 4) + 4)  # Reasonable thread pool size
    
    def create_batch_job(
        self, 
        contents: List[str],
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None,
        user_id: str = None
    ) -> str:
        """Create a new batch processing job."""
        if len(contents) > Config.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(contents)} exceeds maximum {Config.MAX_BATCH_SIZE}")
        
        job_id = str(uuid.uuid4())
        
        job_info = {
            "job_id": job_id,
            "user_id": user_id,
            "total_items": len(contents),
            "processed_items": 0,
            "status": "pending",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "results": [],
            "errors": [],
            "progress_percent": 0.0
        }
        
        self.active_jobs[job_id] = job_info
        
        # Record batch request metrics
        metrics_collector.record_batch_request(len(contents))
        
        logger.info(f"Created batch job {job_id} with {len(contents)} items for user {user_id}")
        
        return job_id
    
    async def process_batch_async(
        self,
        job_id: str,
        contents: List[str],
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Process batch asynchronously with parallel processing."""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job_info = self.active_jobs[job_id]
        job_info["status"] = "processing"
        job_info["started_at"] = datetime.now()
        
        logger.info(f"Starting batch processing for job {job_id}")
        
        try:
            # Process items in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(
                        self._process_single_item,
                        content,
                        percentages,
                        thresholds,
                        probability_thresholds,
                        index
                    ): index
                    for index, content in enumerate(contents)
                }
                
                # Collect results as they complete
                results = [None] * len(contents)  # Pre-allocate results list
                
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                        
                        # Update progress
                        job_info["processed_items"] += 1
                        job_info["progress_percent"] = (
                            job_info["processed_items"] / job_info["total_items"] * 100
                        )
                        
                        logger.debug(f"Job {job_id}: Processed item {index + 1}/{len(contents)}")
                        
                    except Exception as e:
                        error_info = {
                            "index": index,
                            "content_preview": contents[index][:100] + "..." if len(contents[index]) > 100 else contents[index],
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                        job_info["errors"].append(error_info)
                        results[index] = {"error": str(e), "index": index}
                        
                        job_info["processed_items"] += 1
                        job_info["progress_percent"] = (
                            job_info["processed_items"] / job_info["total_items"] * 100
                        )
                        
                        logger.error(f"Job {job_id}: Error processing item {index}: {e}")
            
            # Filter out None results and compile final results
            successful_results = [r for r in results if r is not None and "error" not in r]
            error_results = [r for r in results if r is not None and "error" in r]
            
            job_info["results"] = successful_results
            job_info["status"] = "completed"
            job_info["completed_at"] = datetime.now()
            job_info["progress_percent"] = 100.0
            
            # Calculate processing time
            processing_time = (job_info["completed_at"] - job_info["started_at"]).total_seconds()
            
            logger.info(
                f"Batch job {job_id} completed: {len(successful_results)} successful, "
                f"{len(error_results)} errors, {processing_time:.2f}s"
            )
            
            return {
                "job_id": job_id,
                "status": "completed",
                "total_items": len(contents),
                "successful_items": len(successful_results),
                "failed_items": len(error_results),
                "processing_time_seconds": processing_time,
                "results": successful_results,
                "errors": error_results
            }
            
        except Exception as e:
            job_info["status"] = "failed"
            job_info["completed_at"] = datetime.now()
            job_info["errors"].append({
                "error": f"Batch processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.error(f"Batch job {job_id} failed: {e}")
            raise
    
    def _process_single_item(
        self,
        content: str,
        percentages: Optional[List[float]],
        thresholds: Optional[List[int]],
        probability_thresholds: Optional[Dict[str, int]],
        index: int
    ) -> Dict[str, Any]:
        """Process a single content item with caching support."""
        try:
            # Check cache first
            cached_result = cache_manager.get_cached_result(
                content, percentages, thresholds, probability_thresholds
            )
            
            if cached_result:
                metrics_collector.record_cache_operation("get", "hit")
                # Add index and mark as cached
                cached_result["index"] = index
                cached_result["from_cache"] = True
                return cached_result
            
            metrics_collector.record_cache_operation("get", "miss")
            
            # Process with AI
            result = self.moderation_service.moderate_content(
                content=content,
                percentages=percentages,
                thresholds=thresholds,
                probability_thresholds=probability_thresholds
            )
            
            # Record AI call
            metrics_collector.record_ai_call("success")
            
            # Cache the result
            cache_manager.cache_result(
                content, result, percentages, thresholds, probability_thresholds
            )
            
            # Prepare response (exclude original content for privacy)
            response = {
                "index": index,
                "content_hash": result.get("content_hash", ""),
                "ai_result": result["ai_result"],
                "final_decision": result["final_decision"],
                "reason": result["reason"],
                "word_count": result["word_count"],
                "percentage_used": result["percentage_used"],
                "from_cache": False,
                "processed_at": datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            metrics_collector.record_ai_call("error")
            logger.error(f"Error processing item {index}: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job."""
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id].copy()
        
        # Calculate additional metrics
        if job_info["started_at"] and job_info["status"] == "processing":
            elapsed_time = (datetime.now() - job_info["started_at"]).total_seconds()
            job_info["elapsed_time_seconds"] = elapsed_time
            
            # Estimate remaining time
            if job_info["processed_items"] > 0:
                avg_time_per_item = elapsed_time / job_info["processed_items"]
                remaining_items = job_info["total_items"] - job_info["processed_items"]
                job_info["estimated_remaining_seconds"] = avg_time_per_item * remaining_items
        
        # Don't include full results in status (only counts)
        if "results" in job_info:
            job_info["results_count"] = len(job_info["results"])
            del job_info["results"]  # Remove full results to keep response small
        
        return job_info
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get full results of a completed batch job."""
        if job_id not in self.active_jobs:
            return None
        
        job_info = self.active_jobs[job_id]
        
        if job_info["status"] not in ["completed", "failed"]:
            return {
                "job_id": job_id,
                "status": job_info["status"],
                "message": "Job not yet completed"
            }
        
        return {
            "job_id": job_id,
            "status": job_info["status"],
            "total_items": job_info["total_items"],
            "processed_items": job_info["processed_items"],
            "results": job_info.get("results", []),
            "errors": job_info.get("errors", []),
            "created_at": job_info["created_at"].isoformat(),
            "started_at": job_info["started_at"].isoformat() if job_info["started_at"] else None,
            "completed_at": job_info["completed_at"].isoformat() if job_info["completed_at"] else None
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs to prevent memory leaks."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job_info in self.active_jobs.items():
            if (job_info["status"] in ["completed", "failed"] and 
                job_info.get("completed_at") and 
                job_info["completed_at"] < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            logger.info(f"Cleaned up old job {job_id}")
        
        return len(jobs_to_remove)
    
    def get_active_jobs_summary(self) -> Dict[str, Any]:
        """Get summary of all active jobs."""
        summary = {
            "total_jobs": len(self.active_jobs),
            "by_status": {},
            "total_items_processing": 0
        }
        
        for job_info in self.active_jobs.values():
            status = job_info["status"]
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            if status == "processing":
                summary["total_items_processing"] += job_info["total_items"]
        
        return summary


# Global batch processor instance
batch_processor = BatchProcessor()
