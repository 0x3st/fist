"""
Semantic-Aware Caching System for FIST Content Moderation System.

This module provides intelligent caching based on semantic similarity including:
- Sentence embedding-based cache keys
- Similarity-based cache retrieval
- Vector database integration
- Intelligent cache invalidation
- Distributed caching support
- Cache analytics and optimization
"""
import logging
import time
import hashlib
import json
import pickle
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import queue

from core.config import Config


class CacheStrategy(Enum):
    """Cache strategy types."""
    EXACT_MATCH = "exact_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID = "hybrid"
    CONTENT_HASH = "content_hash"


class CacheStatus(Enum):
    """Cache entry status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    PENDING = "pending"


@dataclass
class CacheEntry:
    """Individual cache entry."""
    cache_key: str
    content_hash: str
    original_content: str
    moderation_result: Dict[str, Any]
    embedding: Optional[List[float]]
    similarity_threshold: float
    created_at: float
    last_accessed: float
    access_count: int
    ttl: float
    status: CacheStatus
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheHit:
    """Cache hit result."""
    hit: bool
    cache_entry: Optional[CacheEntry]
    similarity_score: float
    retrieval_method: str
    processing_time: float


@dataclass
class CacheAnalytics:
    """Cache performance analytics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    average_similarity_score: float
    average_retrieval_time: float
    storage_usage: int
    active_entries: int
    expired_entries: int
    invalidated_entries: int


class SimpleEmbeddingGenerator:
    """Simple embedding generator for semantic similarity."""

    def __init__(self):
        """Initialize embedding generator."""
        self.logger = logging.getLogger(__name__)

        # Try to import sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.transformers_available = True
            self.logger.info("Sentence transformers available")
        except ImportError:
            self.transformers_available = False
            self.logger.warning("Sentence transformers not available, using simple embeddings")

        # Simple word-based embedding as fallback
        self.vocab = {}
        self.vocab_size = 1000
        self.embedding_dim = 384  # Match sentence transformer dimension

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.transformers_available:
            return self._generate_transformer_embedding(text)
        else:
            return self._generate_simple_embedding(text)

    def _generate_transformer_embedding(self, text: str) -> List[float]:
        """Generate embedding using sentence transformers."""
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            self.logger.warning(f"Transformer embedding failed: {e}")
            return self._generate_simple_embedding(text)

    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate simple word-based embedding."""
        words = text.lower().split()

        # Build vocabulary
        for word in words:
            if word not in self.vocab and len(self.vocab) < self.vocab_size:
                self.vocab[word] = len(self.vocab)

        # Create embedding
        embedding = [0.0] * self.embedding_dim

        for word in words:
            if word in self.vocab:
                idx = self.vocab[word] % self.embedding_dim
                embedding[idx] += 1.0

        # Normalize
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


class InMemoryVectorStore:
    """Simple in-memory vector store for semantic search."""

    def __init__(self):
        """Initialize vector store."""
        self.entries = {}  # cache_key -> CacheEntry
        self.embeddings = {}  # cache_key -> embedding
        self.embedding_generator = SimpleEmbeddingGenerator()
        self.logger = logging.getLogger(__name__)

    def add_entry(self, cache_entry: CacheEntry):
        """Add cache entry to vector store."""
        self.entries[cache_entry.cache_key] = cache_entry
        if cache_entry.embedding:
            self.embeddings[cache_entry.cache_key] = cache_entry.embedding
        self.logger.debug(f"Added cache entry {cache_entry.cache_key}")

    def search_similar(self, query_embedding: List[float],
                      similarity_threshold: float = 0.8,
                      limit: int = 1) -> List[Tuple[str, float]]:
        """Search for similar entries."""
        results = []

        for cache_key, embedding in self.embeddings.items():
            if cache_key in self.entries and self.entries[cache_key].status == CacheStatus.ACTIVE:
                similarity = self.embedding_generator.calculate_similarity(query_embedding, embedding)
                if similarity >= similarity_threshold:
                    results.append((cache_key, similarity))

        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def remove_entry(self, cache_key: str):
        """Remove entry from vector store."""
        if cache_key in self.entries:
            del self.entries[cache_key]
        if cache_key in self.embeddings:
            del self.embeddings[cache_key]
        self.logger.debug(f"Removed cache entry {cache_key}")

    def get_entry(self, cache_key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        return self.entries.get(cache_key)

    def get_stats(self) -> Dict[str, int]:
        """Get vector store statistics."""
        active_entries = sum(1 for entry in self.entries.values()
                           if entry.status == CacheStatus.ACTIVE)
        return {
            'total_entries': len(self.entries),
            'active_entries': active_entries,
            'total_embeddings': len(self.embeddings)
        }


class SemanticCacheManager:
    """Advanced semantic cache manager."""

    def __init__(self):
        """Initialize semantic cache manager."""
        self.logger = logging.getLogger(__name__)

        # Cache configuration
        self.default_ttl = Config.CACHE_TTL if hasattr(Config, 'CACHE_TTL') else 3600
        self.default_similarity_threshold = 0.85
        self.max_cache_size = 10000
        self.cleanup_interval = 300  # 5 minutes

        # Storage backends
        self.vector_store = InMemoryVectorStore()
        self.embedding_generator = SimpleEmbeddingGenerator()

        # Analytics
        self.analytics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'similarity_scores': deque(maxlen=1000),
            'retrieval_times': deque(maxlen=1000)
        }

        # Background cleanup
        self.cleanup_thread = None
        self.stop_cleanup = threading.Event()
        self._start_cleanup_thread()

        self.logger.info("Semantic cache manager initialized")

    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.stop_cleanup.clear()
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            self.logger.info("Started cache cleanup thread")

    def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self.stop_cleanup.is_set():
            try:
                self._cleanup_expired_entries()
                self._enforce_cache_size_limit()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait longer on error

    def _cleanup_expired_entries(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = []

        for cache_key, entry in self.vector_store.entries.items():
            if entry.status == CacheStatus.ACTIVE:
                if current_time - entry.created_at > entry.ttl:
                    entry.status = CacheStatus.EXPIRED
                    expired_keys.append(cache_key)

        for key in expired_keys:
            self.vector_store.remove_entry(key)

        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _enforce_cache_size_limit(self):
        """Enforce maximum cache size by removing oldest entries."""
        stats = self.vector_store.get_stats()
        if stats['active_entries'] > self.max_cache_size:
            # Get all active entries sorted by last access time
            active_entries = [
                (key, entry) for key, entry in self.vector_store.entries.items()
                if entry.status == CacheStatus.ACTIVE
            ]
            active_entries.sort(key=lambda x: x[1].last_accessed)

            # Remove oldest entries
            entries_to_remove = len(active_entries) - self.max_cache_size
            for i in range(entries_to_remove):
                key, entry = active_entries[i]
                entry.status = CacheStatus.INVALIDATED
                self.vector_store.remove_entry(key)

            self.logger.info(f"Removed {entries_to_remove} entries to enforce size limit")

    def _generate_cache_key(self, content: str, strategy: CacheStrategy) -> str:
        """Generate cache key based on strategy."""
        if strategy == CacheStrategy.EXACT_MATCH:
            return hashlib.sha256(content.encode()).hexdigest()
        elif strategy == CacheStrategy.CONTENT_HASH:
            # Normalize content for hashing
            normalized = ' '.join(content.lower().split())
            return hashlib.sha256(normalized.encode()).hexdigest()
        else:
            # For semantic strategies, use content hash as base key
            return hashlib.sha256(content.encode()).hexdigest()

    def get_cached_result(self, content: str,
                         strategy: CacheStrategy = CacheStrategy.HYBRID,
                         similarity_threshold: Optional[float] = None) -> CacheHit:
        """
        Retrieve cached moderation result.

        Args:
            content: Content to check
            strategy: Cache retrieval strategy
            similarity_threshold: Minimum similarity for semantic matching

        Returns:
            Cache hit result
        """
        start_time = time.time()
        self.analytics['total_requests'] += 1

        if similarity_threshold is None:
            similarity_threshold = self.default_similarity_threshold

        # Try exact match first
        cache_key = self._generate_cache_key(content, CacheStrategy.EXACT_MATCH)
        cache_entry = self.vector_store.get_entry(cache_key)

        if cache_entry and cache_entry.status == CacheStatus.ACTIVE:
            cache_entry.last_accessed = time.time()
            cache_entry.access_count += 1

            processing_time = time.time() - start_time
            self.analytics['cache_hits'] += 1
            self.analytics['retrieval_times'].append(processing_time)

            return CacheHit(
                hit=True,
                cache_entry=cache_entry,
                similarity_score=1.0,
                retrieval_method="exact_match",
                processing_time=processing_time
            )

        # Try semantic similarity if strategy allows
        if strategy in [CacheStrategy.SEMANTIC_SIMILARITY, CacheStrategy.HYBRID]:
            query_embedding = self.embedding_generator.generate_embedding(content)
            similar_entries = self.vector_store.search_similar(
                query_embedding, similarity_threshold, limit=1
            )

            if similar_entries:
                similar_key, similarity_score = similar_entries[0]
                cache_entry = self.vector_store.get_entry(similar_key)

                if cache_entry and cache_entry.status == CacheStatus.ACTIVE:
                    cache_entry.last_accessed = time.time()
                    cache_entry.access_count += 1

                    processing_time = time.time() - start_time
                    self.analytics['cache_hits'] += 1
                    self.analytics['similarity_scores'].append(similarity_score)
                    self.analytics['retrieval_times'].append(processing_time)

                    return CacheHit(
                        hit=True,
                        cache_entry=cache_entry,
                        similarity_score=similarity_score,
                        retrieval_method="semantic_similarity",
                        processing_time=processing_time
                    )

        # Cache miss
        processing_time = time.time() - start_time
        self.analytics['cache_misses'] += 1
        self.analytics['retrieval_times'].append(processing_time)

        return CacheHit(
            hit=False,
            cache_entry=None,
            similarity_score=0.0,
            retrieval_method="none",
            processing_time=processing_time
        )

    def store_result(self, content: str, moderation_result: Dict[str, Any],
                    ttl: Optional[float] = None,
                    similarity_threshold: Optional[float] = None) -> str:
        """
        Store moderation result in cache.

        Args:
            content: Original content
            moderation_result: Moderation result to cache
            ttl: Time to live in seconds
            similarity_threshold: Similarity threshold for this entry

        Returns:
            Cache key
        """
        if ttl is None:
            ttl = self.default_ttl

        if similarity_threshold is None:
            similarity_threshold = self.default_similarity_threshold

        # Generate cache key and embedding
        cache_key = self._generate_cache_key(content, CacheStrategy.EXACT_MATCH)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        embedding = self.embedding_generator.generate_embedding(content)

        # Create cache entry
        cache_entry = CacheEntry(
            cache_key=cache_key,
            content_hash=content_hash,
            original_content=content,
            moderation_result=moderation_result,
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=0,
            ttl=ttl,
            status=CacheStatus.ACTIVE,
            metadata={
                'content_length': len(content),
                'result_type': type(moderation_result).__name__
            }
        )

        # Store in vector store
        self.vector_store.add_entry(cache_entry)

        self.logger.debug(f"Stored cache entry {cache_key}")
        return cache_key

    def invalidate_cache(self, pattern: Optional[str] = None,
                        content_hash: Optional[str] = None,
                        cache_key: Optional[str] = None):
        """
        Invalidate cache entries.

        Args:
            pattern: Pattern to match against content
            content_hash: Specific content hash to invalidate
            cache_key: Specific cache key to invalidate
        """
        invalidated_count = 0

        if cache_key:
            # Invalidate specific key
            entry = self.vector_store.get_entry(cache_key)
            if entry:
                entry.status = CacheStatus.INVALIDATED
                self.vector_store.remove_entry(cache_key)
                invalidated_count = 1

        elif content_hash:
            # Invalidate by content hash
            for key, entry in list(self.vector_store.entries.items()):
                if entry.content_hash == content_hash:
                    entry.status = CacheStatus.INVALIDATED
                    self.vector_store.remove_entry(key)
                    invalidated_count += 1

        elif pattern:
            # Invalidate by pattern matching
            for key, entry in list(self.vector_store.entries.items()):
                if pattern.lower() in entry.original_content.lower():
                    entry.status = CacheStatus.INVALIDATED
                    self.vector_store.remove_entry(key)
                    invalidated_count += 1

        self.logger.info(f"Invalidated {invalidated_count} cache entries")

    def get_analytics(self) -> CacheAnalytics:
        """Get cache performance analytics."""
        total_requests = self.analytics['total_requests']
        cache_hits = self.analytics['cache_hits']
        cache_misses = self.analytics['cache_misses']

        hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0

        avg_similarity = (sum(self.analytics['similarity_scores']) /
                         len(self.analytics['similarity_scores'])) if self.analytics['similarity_scores'] else 0.0

        avg_retrieval_time = (sum(self.analytics['retrieval_times']) /
                             len(self.analytics['retrieval_times'])) if self.analytics['retrieval_times'] else 0.0

        stats = self.vector_store.get_stats()

        return CacheAnalytics(
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            average_similarity_score=avg_similarity,
            average_retrieval_time=avg_retrieval_time,
            storage_usage=stats['total_entries'],
            active_entries=stats['active_entries'],
            expired_entries=0,  # Cleaned up automatically
            invalidated_entries=0  # Cleaned up automatically
        )

    def optimize_cache(self):
        """Optimize cache performance."""
        # Analyze access patterns
        access_counts = {}
        for entry in self.vector_store.entries.values():
            if entry.status == CacheStatus.ACTIVE:
                access_counts[entry.cache_key] = entry.access_count

        # Identify frequently accessed entries
        if access_counts:
            avg_access = sum(access_counts.values()) / len(access_counts)
            frequently_accessed = [key for key, count in access_counts.items()
                                 if count > avg_access * 2]

            self.logger.info(f"Cache optimization: {len(frequently_accessed)} frequently accessed entries")

        # Force cleanup
        self._cleanup_expired_entries()
        self._enforce_cache_size_limit()

    def stop(self):
        """Stop cache manager and cleanup threads."""
        self.stop_cleanup.set()
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        self.logger.info("Semantic cache manager stopped")


# Global instance
_semantic_cache_manager: Optional[SemanticCacheManager] = None


def get_semantic_cache_manager() -> SemanticCacheManager:
    """Get global semantic cache manager instance."""
    global _semantic_cache_manager
    if _semantic_cache_manager is None:
        _semantic_cache_manager = SemanticCacheManager()
    return _semantic_cache_manager


def get_cached_moderation_result(content: str,
                                similarity_threshold: float = 0.85) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get cached moderation result.

    Args:
        content: Content to check
        similarity_threshold: Minimum similarity for semantic matching

    Returns:
        Cached moderation result or None
    """
    cache_manager = get_semantic_cache_manager()
    cache_hit = cache_manager.get_cached_result(content,
                                              CacheStrategy.HYBRID,
                                              similarity_threshold)

    if cache_hit.hit and cache_hit.cache_entry:
        return cache_hit.cache_entry.moderation_result

    return None


def store_moderation_result(content: str, result: Dict[str, Any], ttl: int = 3600):
    """
    Convenience function to store moderation result.

    Args:
        content: Original content
        result: Moderation result
        ttl: Time to live in seconds
    """
    cache_manager = get_semantic_cache_manager()
    cache_manager.store_result(content, result, ttl)
