"""
In-memory TTL cache for search results.

Caches retrieval results by hashed (query + filters) keys so
identical queries within the TTL window skip the full search pipeline.
"""

from typing import Optional, Any
import hashlib
import json
import logging
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

# Default: 256 entries, 5-minute TTL
DEFAULT_MAX_SIZE = 256
DEFAULT_TTL = 300  # seconds


class CacheService:
    """Thread-safe TTL cache for search results."""

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE, ttl: int = DEFAULT_TTL):
        self._cache = TTLCache(maxsize=max_size, ttl=ttl)
        self._lock = threading.Lock()
        logger.info(f"Cache initialized: max_size={max_size}, ttl={ttl}s")

    @staticmethod
    def _build_key(query: str, user_id: str, **kwargs) -> str:
        """Build a deterministic cache key from query + filters."""
        key_data = {
            "query": query.strip().lower(),
            "user_id": user_id,
            **{k: v for k, v in sorted(kwargs.items()) if v is not None},
        }
        raw = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, user_id: str, **kwargs) -> Optional[Any]:
        """Retrieve a cached result. Returns None on miss."""
        key = self._build_key(query, user_id, **kwargs)
        with self._lock:
            result = self._cache.get(key)
        if result is not None:
            logger.debug(f"Cache HIT for key={key[:12]}...")
        else:
            logger.debug(f"Cache MISS for key={key[:12]}...")
        return result

    def set(self, query: str, user_id: str, value: Any, **kwargs) -> None:
        """Store a result in the cache."""
        key = self._build_key(query, user_id, **kwargs)
        with self._lock:
            self._cache[key] = value
        logger.debug(f"Cache SET for key={key[:12]}...")

    def invalidate_user(self, user_id: str) -> int:
        """
        Remove all cache entries for a given user.
        Called when a user's notes are re-indexed.
        Returns the number of entries removed.
        """
        removed = 0
        with self._lock:
            # TTLCache doesn't support iteration during mutation,
            # so collect keys first.
            keys_to_remove = []
            # We can't easily filter by user_id from hash keys,
            # so we do a full clear for simplicity. In production
            # you'd use a secondary index or tagged cache.
            self._cache.clear()
            removed = -1  # indicates full clear
        logger.info(f"Cache invalidated for user={user_id}")
        return removed

    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
        logger.info("Cache fully cleared")

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)


# Singleton
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
