"""
FIST Content Moderation Python Client Library

A Python client library for easy integration with the FIST Content Moderation API.
Provides simple methods for content moderation, batch processing, and monitoring.

Usage:
    from fist_client import FistClient
    
    client = FistClient(
        token="fist_your_token_here",
        base_url="https://your-fist-api.com"
    )
    
    # Single content moderation
    result = client.moderate_content("Some text to moderate")
    
    # Batch processing
    results = client.moderate_batch(["text1", "text2", "text3"])
"""
import requests
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModerationResult:
    """Result of content moderation."""
    moderation_id: str
    content_hash: str
    inappropriate_probability: int
    ai_reason: str
    final_decision: str  # A, R, or M
    reason: str
    word_count: int
    percentage_used: float
    created_at: str
    from_cache: bool = False


@dataclass
class BatchJob:
    """Batch processing job information."""
    job_id: str
    status: str
    total_items: int
    processed_items: int
    progress_percent: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    background_task_id: Optional[str] = None


class FistClientError(Exception):
    """Base exception for FIST client errors."""
    pass


class AuthenticationError(FistClientError):
    """Authentication failed."""
    pass


class APIError(FistClientError):
    """API request failed."""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class FistClient:
    """
    Python client for FIST Content Moderation API.
    
    Provides easy-to-use methods for content moderation, batch processing,
    and system monitoring with automatic error handling and retries.
    """
    
    def __init__(
        self, 
        token: str, 
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize FIST client.
        
        Args:
            token: API token (should start with 'fist_')
            base_url: Base URL of the FIST API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Validate token format
        if not token.startswith('fist_'):
            raise ValueError("Token must start with 'fist_'")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'FIST-Python-Client/1.0.0'
        })
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=self.timeout)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired token")
                
                # Handle other client/server errors
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_message = error_data.get('detail', f'HTTP {response.status_code}')
                    except:
                        error_message = f'HTTP {response.status_code}: {response.text}'
                    
                    raise APIError(
                        error_message, 
                        status_code=response.status_code,
                        response_data=error_data if 'error_data' in locals() else None
                    )
                
                return response.json()
                
            except (requests.exceptions.RequestException, APIError) as e:
                if attempt == self.max_retries:
                    raise
                
                if isinstance(e, APIError) and e.status_code < 500:
                    # Don't retry client errors (4xx)
                    raise
                
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        raise APIError("Max retries exceeded")
    
    def moderate_content(
        self,
        content: str,
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> ModerationResult:
        """
        Moderate a single piece of content.
        
        Args:
            content: Text content to moderate
            percentages: Custom percentages for content piercing
            thresholds: Custom word count thresholds
            probability_thresholds: Custom probability thresholds
            
        Returns:
            ModerationResult object with moderation details
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        
        data = {"content": content}
        if percentages is not None:
            data["percentages"] = percentages
        if thresholds is not None:
            data["thresholds"] = thresholds
        if probability_thresholds is not None:
            data["probability_thresholds"] = probability_thresholds
        
        response = self._make_request('POST', '/api/moderate', data=data)
        
        result_data = response['result']
        return ModerationResult(
            moderation_id=result_data['moderation_id'],
            content_hash=result_data['content_hash'],
            inappropriate_probability=result_data['ai_result']['inappropriate_probability'],
            ai_reason=result_data['ai_result']['reason'],
            final_decision=result_data['final_decision'],
            reason=result_data['reason'],
            word_count=result_data['word_count'],
            percentage_used=result_data['percentage_used'],
            created_at=result_data['created_at']
        )
    
    def moderate_batch(
        self,
        contents: List[str],
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None,
        background: bool = False,
        poll_interval: float = 2.0,
        max_wait_time: int = 300
    ) -> Union[List[ModerationResult], BatchJob]:
        """
        Moderate multiple pieces of content in batch.
        
        Args:
            contents: List of text content to moderate
            percentages: Custom percentages for content piercing
            thresholds: Custom word count thresholds
            probability_thresholds: Custom probability thresholds
            background: Process in background (returns BatchJob for polling)
            poll_interval: Polling interval for background jobs (seconds)
            max_wait_time: Maximum time to wait for background jobs (seconds)
            
        Returns:
            List of ModerationResult objects (if background=False)
            or BatchJob object (if background=True)
        """
        if not contents:
            raise ValueError("Contents list cannot be empty")
        
        if len(contents) > 100:
            raise ValueError("Batch size cannot exceed 100 items")
        
        data = {
            "contents": contents,
            "background": background
        }
        if percentages is not None:
            data["percentages"] = percentages
        if thresholds is not None:
            data["thresholds"] = thresholds
        if probability_thresholds is not None:
            data["probability_thresholds"] = probability_thresholds
        
        response = self._make_request('POST', '/api/moderate/batch', data=data)
        
        if background:
            # Return BatchJob for polling
            batch_job = BatchJob(
                job_id=response['job_id'],
                status=response['status'],
                total_items=response['total_items'],
                processed_items=response['processed_items'],
                progress_percent=response['progress_percent'],
                created_at=response['created_at'],
                background_task_id=response.get('background_task_id')
            )
            
            # Wait for completion if requested
            if max_wait_time > 0:
                return self._wait_for_batch_completion(batch_job.job_id, poll_interval, max_wait_time)
            
            return batch_job
        else:
            # Return results directly
            results = []
            for result_data in response.get('results', []):
                results.append(ModerationResult(
                    moderation_id=result_data['moderation_id'],
                    content_hash=result_data['content_hash'],
                    inappropriate_probability=result_data['ai_result']['inappropriate_probability'],
                    ai_reason=result_data['ai_result']['reason'],
                    final_decision=result_data['final_decision'],
                    reason=result_data['reason'],
                    word_count=result_data['word_count'],
                    percentage_used=result_data['percentage_used'],
                    created_at=result_data['created_at'],
                    from_cache=result_data.get('from_cache', False)
                ))
            return results
    
    def get_batch_status(self, job_id: str) -> BatchJob:
        """
        Get status of a batch processing job.
        
        Args:
            job_id: Batch job ID
            
        Returns:
            BatchJob object with current status
        """
        response = self._make_request('GET', f'/api/moderate/batch/{job_id}/status')
        
        return BatchJob(
            job_id=response['job_id'],
            status=response['status'],
            total_items=response['total_items'],
            processed_items=response['processed_items'],
            progress_percent=response['progress_percent'],
            created_at=response.get('created_at', ''),
            started_at=response.get('started_at'),
            completed_at=response.get('completed_at')
        )
    
    def get_batch_results(self, job_id: str) -> List[ModerationResult]:
        """
        Get results of a completed batch job.
        
        Args:
            job_id: Batch job ID
            
        Returns:
            List of ModerationResult objects
        """
        response = self._make_request('GET', f'/api/moderate/batch/{job_id}/results')
        
        results = []
        for result_data in response.get('results', []):
            results.append(ModerationResult(
                moderation_id=result_data['moderation_id'],
                content_hash=result_data['content_hash'],
                inappropriate_probability=result_data['ai_result']['inappropriate_probability'],
                ai_reason=result_data['ai_result']['reason'],
                final_decision=result_data['final_decision'],
                reason=result_data['reason'],
                word_count=result_data['word_count'],
                percentage_used=result_data['percentage_used'],
                created_at=result_data['created_at'],
                from_cache=result_data.get('from_cache', False)
            ))
        return results
    
    def _wait_for_batch_completion(
        self, 
        job_id: str, 
        poll_interval: float, 
        max_wait_time: int
    ) -> List[ModerationResult]:
        """Wait for batch job completion and return results."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_batch_status(job_id)
            
            if status.status == 'completed':
                return self.get_batch_results(job_id)
            elif status.status == 'failed':
                raise APIError(f"Batch job {job_id} failed")
            
            time.sleep(poll_interval)
        
        raise APIError(f"Batch job {job_id} did not complete within {max_wait_time} seconds")
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            Dictionary with health check results
        """
        return self._make_request('GET', '/api/health')
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        return self._make_request('GET', '/api/metrics')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self._make_request('GET', '/api/cache/stats')
    
    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the system cache.
        
        Returns:
            Dictionary with clear operation results
        """
        return self._make_request('DELETE', '/api/cache/clear')
    
    def test_connection(self) -> bool:
        """
        Test connection to the FIST API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            health = self.get_health()
            return health.get('status') in ['healthy', 'warning']
        except:
            return False


# Convenience functions for quick usage
def moderate_content(
    content: str, 
    token: str, 
    base_url: str = "http://localhost:8000",
    **kwargs
) -> ModerationResult:
    """
    Quick function to moderate a single piece of content.
    
    Args:
        content: Text content to moderate
        token: API token
        base_url: Base URL of the FIST API
        **kwargs: Additional arguments for moderation
        
    Returns:
        ModerationResult object
    """
    client = FistClient(token=token, base_url=base_url)
    return client.moderate_content(content, **kwargs)


def moderate_batch(
    contents: List[str], 
    token: str, 
    base_url: str = "http://localhost:8000",
    **kwargs
) -> List[ModerationResult]:
    """
    Quick function to moderate multiple pieces of content.
    
    Args:
        contents: List of text content to moderate
        token: API token
        base_url: Base URL of the FIST API
        **kwargs: Additional arguments for moderation
        
    Returns:
        List of ModerationResult objects
    """
    client = FistClient(token=token, base_url=base_url)
    return client.moderate_batch(contents, **kwargs)


# Example usage
if __name__ == "__main__":
    # Example usage of the FIST client
    client = FistClient(
        token="fist_your_token_here",
        base_url="http://localhost:8000"
    )
    
    # Test connection
    if client.test_connection():
        print("✅ Connected to FIST API successfully")
        
        # Single content moderation
        result = client.moderate_content("This is a test message")
        print(f"Moderation result: {result.final_decision} ({result.inappropriate_probability}%)")
        
        # Batch processing
        contents = ["Message 1", "Message 2", "Message 3"]
        results = client.moderate_batch(contents)
        print(f"Batch processed {len(results)} items")
        
        # System health
        health = client.get_health()
        print(f"System health: {health['status']}")
        
    else:
        print("❌ Failed to connect to FIST API")
