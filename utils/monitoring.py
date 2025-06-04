"""
Performance monitoring and metrics collection for FIST Content Moderation System.

This module provides comprehensive monitoring capabilities including:
- Response time tracking
- Cache hit rate monitoring
- System resource monitoring
- API endpoint metrics
- Health checks
"""
import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import wraps
from core.config import Config

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available. Metrics collection will be limited.")


class MetricsCollector:
    """Collects and manages performance metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.enabled = Config.ENABLE_METRICS
        self.start_time = datetime.now()

        # In-memory metrics storage (fallback when Prometheus not available)
        self.metrics = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "response_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "ai_calls": 0,
            "batch_requests": 0
        }

        if PROMETHEUS_AVAILABLE and self.enabled:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        self.request_count = Counter(
            'fist_requests_total',
            'Total number of requests',
            ['endpoint', 'method', 'status']
        )

        self.request_duration = Histogram(
            'fist_request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method']
        )

        self.cache_operations = Counter(
            'fist_cache_operations_total',
            'Cache operations',
            ['operation', 'result']
        )

        self.ai_calls = Counter(
            'fist_ai_calls_total',
            'AI API calls',
            ['status']
        )

        self.system_memory = Gauge(
            'fist_system_memory_usage_bytes',
            'System memory usage in bytes'
        )

        self.system_cpu = Gauge(
            'fist_system_cpu_usage_percent',
            'System CPU usage percentage'
        )

        self.active_connections = Gauge(
            'fist_active_connections',
            'Number of active connections'
        )

        logger.info("Prometheus metrics initialized")

    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics."""
        if not self.enabled:
            return

        # Update in-memory metrics
        self.metrics["requests_total"] += 1
        endpoint_key = f"{method} {endpoint}"
        self.metrics["requests_by_endpoint"][endpoint_key] = \
            self.metrics["requests_by_endpoint"].get(endpoint_key, 0) + 1
        self.metrics["response_times"].append(duration)

        # Keep only last 1000 response times to prevent memory growth
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        if status_code >= 400:
            self.metrics["errors"] += 1

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.request_count.labels(
                endpoint=endpoint,
                method=method,
                status=str(status_code)
            ).inc()

            self.request_duration.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        if not self.enabled:
            return

        # Update in-memory metrics
        if operation == "get" and result == "hit":
            self.metrics["cache_hits"] += 1
        elif operation == "get" and result == "miss":
            self.metrics["cache_misses"] += 1

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.cache_operations.labels(operation=operation, result=result).inc()

    def record_ai_call(self, status: str = "success"):
        """Record AI API call metrics."""
        if not self.enabled:
            return

        self.metrics["ai_calls"] += 1

        if PROMETHEUS_AVAILABLE:
            self.ai_calls.labels(status=status).inc()

    def record_batch_request(self, batch_size: int):
        """Record batch processing metrics."""
        if not self.enabled:
            return

        self.metrics["batch_requests"] += 1
        self.metrics["batch_size_total"] = self.metrics.get("batch_size_total", 0) + batch_size

    def update_system_metrics(self):
        """Update system resource metrics."""
        if not self.enabled:
            return

        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()

            if PROMETHEUS_AVAILABLE:
                self.system_memory.set(memory.used)
                self.system_cpu.set(cpu_percent)
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        if not self.enabled:
            return {"enabled": False}

        try:
            # Calculate cache hit rate
            total_cache_ops = self.metrics["cache_hits"] + self.metrics["cache_misses"]
            cache_hit_rate = (
                self.metrics["cache_hits"] / total_cache_ops * 100
                if total_cache_ops > 0 else 0
            )

            # Calculate average response time
            response_times = self.metrics["response_times"]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            # Get system info
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()

            # Calculate uptime
            uptime = datetime.now() - self.start_time

            return {
                "enabled": True,
                "uptime_seconds": int(uptime.total_seconds()),
                "requests": {
                    "total": self.metrics["requests_total"],
                    "by_endpoint": self.metrics["requests_by_endpoint"],
                    "errors": self.metrics["errors"],
                    "error_rate": (
                        self.metrics["errors"] / self.metrics["requests_total"] * 100
                        if self.metrics["requests_total"] > 0 else 0
                    )
                },
                "performance": {
                    "avg_response_time_ms": round(avg_response_time * 1000, 2),
                    "cache_hit_rate": round(cache_hit_rate, 2),
                    "ai_calls": self.metrics["ai_calls"],
                    "batch_requests": self.metrics["batch_requests"]
                },
                "system": {
                    "memory_usage_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "cpu_usage_percent": cpu_percent
                },
                "cache": {
                    "hits": self.metrics["cache_hits"],
                    "misses": self.metrics["cache_misses"],
                    "hit_rate": round(cache_hit_rate, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"enabled": True, "error": str(e)}

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"

        try:
            # Update system metrics before generating output
            self.update_system_metrics()
            return generate_latest()
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}\n"

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        try:
            # Check system resources
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()

            health["checks"]["memory"] = {
                "status": "healthy" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent
            }

            health["checks"]["cpu"] = {
                "status": "healthy" if cpu_percent < 80 else "warning",
                "usage_percent": cpu_percent
            }

            # Check cache health
            from utils.cache import cache_manager
            cache_healthy = cache_manager.health_check()
            health["checks"]["cache"] = {
                "status": "healthy" if cache_healthy else "unhealthy",
                "enabled": cache_manager.enabled
            }

            # Overall status
            if any(check["status"] == "unhealthy" for check in health["checks"].values()):
                health["status"] = "unhealthy"
            elif any(check["status"] == "warning" for check in health["checks"].values()):
                health["status"] = "warning"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health


def monitor_endpoint(endpoint_name: str):
    """Decorator to monitor API endpoint performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_request(
                    endpoint=endpoint_name,
                    method="POST",  # Most FIST endpoints are POST
                    status_code=status_code,
                    duration=duration
                )

        return wrapper
    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()
