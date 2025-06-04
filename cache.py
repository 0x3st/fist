"""
Redis-based caching system for FIST Content Moderation System.

This module provides caching functionality to avoid duplicate AI calls
for frequently moderated content, improving performance and reducing costs.
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Caching will be disabled.")


class CacheManager:
    """Redis-based cache manager for moderation results."""
    
    def __init__(self):
        """Initialize cache manager."""
        self.enabled = Config.ENABLE_CACHE and REDIS_AVAILABLE
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    Config.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.enabled = False
                self.redis_client = None
    
    def _generate_cache_key(self, content: str, config_params: Dict[str, Any]) -> str:
        """Generate cache key based on content and configuration."""
        # Create a hash of content + configuration parameters
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        config_str = json.dumps(config_params, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode('utf-8')).hexdigest()
        
        return f"fist:moderation:{content_hash}:{config_hash[:16]}"
    
    def get_cached_result(
        self, 
        content: str, 
        percentages: Optional[list] = None,
        thresholds: Optional[list] = None,
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached moderation result if available."""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            config_params = {
                "percentages": percentages or Config.DEFAULT_PERCENTAGES,
                "thresholds": thresholds or Config.DEFAULT_THRESHOLDS,
                "probability_thresholds": probability_thresholds or Config.DEFAULT_PROBABILITY_THRESHOLDS
            }
            
            cache_key = self._generate_cache_key(content, config_params)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key[:32]}...")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for key: {cache_key[:32]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_result(
        self, 
        content: str, 
        result: Dict[str, Any],
        percentages: Optional[list] = None,
        thresholds: Optional[list] = None,
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> bool:
        """Cache moderation result."""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            config_params = {
                "percentages": percentages or Config.DEFAULT_PERCENTAGES,
                "thresholds": thresholds or Config.DEFAULT_THRESHOLDS,
                "probability_thresholds": probability_thresholds or Config.DEFAULT_PROBABILITY_THRESHOLDS
            }
            
            cache_key = self._generate_cache_key(content, config_params)
            
            # Store only essential data to save memory
            cache_data = {
                "ai_result": result["ai_result"],
                "final_decision": result["final_decision"],
                "reason": result["reason"],
                "word_count": result["word_count"],
                "percentage_used": result["percentage_used"],
                "cached_at": result.get("created_at", "unknown")
            }
            
            self.redis_client.setex(
                cache_key, 
                Config.CACHE_TTL, 
                json.dumps(cache_data)
            )
            
            logger.info(f"Cached result for key: {cache_key[:32]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            return False
    
    def clear_cache(self, pattern: str = "fist:moderation:*") -> int:
        """Clear cache entries matching pattern."""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled or not self.redis_client:
            return {"enabled": False, "error": "Cache not available"}
        
        try:
            info = self.redis_client.info()
            keys_count = len(self.redis_client.keys("fist:moderation:*"))
            
            return {
                "enabled": True,
                "connected": True,
                "keys_count": keys_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
    
    def health_check(self) -> bool:
        """Check if cache is healthy."""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Global cache manager instance
cache_manager = CacheManager()
