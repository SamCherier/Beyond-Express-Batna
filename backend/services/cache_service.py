"""Redis Cache Service — Smart TTL Caching
Provides a simple async caching layer for dashboard data.
Gracefully degrades if Redis is unavailable (no crash).
"""
import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# TTL presets (seconds)
TTL_DASHBOARD_STATS = 60       # 1 min — stats refresh frequently
TTL_REVENUE = 120              # 2 min — revenue changes less often
TTL_ORDERS_BY_STATUS = 60      # 1 min
TTL_WAREHOUSE = 30             # 30s — warehouse data is critical
TTL_SHORT = 15                 # 15s — for near-real-time data


class RedisCacheService:
    """Async-compatible Redis cache. Falls back silently if Redis is down."""

    def __init__(self):
        self._redis = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            import redis
            url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2)
            self._redis.ping()
            self._available = True
            logger.info(f"Redis cache connected ({url})")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[Any]:
        if not self._available:
            return None
        try:
            raw = self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 60):
        if not self._available:
            return
        try:
            self._redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")

    def delete(self, key: str):
        if not self._available:
            return
        try:
            self._redis.delete(key)
        except Exception:
            pass

    def invalidate_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'dashboard:*')."""
        if not self._available:
            return
        try:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
        except Exception:
            pass

    def get_info(self) -> dict:
        if not self._available:
            return {"available": False}
        try:
            info = self._redis.info("memory")
            keys_count = self._redis.dbsize()
            return {
                "available": True,
                "keys": keys_count,
                "used_memory": info.get("used_memory_human", "?"),
                "max_memory": info.get("maxmemory_human", "unlimited"),
            }
        except Exception:
            return {"available": False}


# Singleton
cache = RedisCacheService()
