"""
Cache Service - LOBINHO-BET
============================
Redis caching for API responses and computed data.
"""

import json
import hashlib
from datetime import timedelta
from typing import Optional, Any, Callable
from functools import wraps
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheService:
    """
    Redis-based caching service.
    Falls back to in-memory cache if Redis unavailable.
    """

    # Default TTLs
    TTL_SHORT = 60  # 1 minute - live data
    TTL_MEDIUM = 300  # 5 minutes - odds data
    TTL_LONG = 3600  # 1 hour - static data
    TTL_VERY_LONG = 86400  # 24 hours - historical data

    def __init__(self, redis_url: Optional[str] = None):
        self._redis: Optional[redis.Redis] = None
        self._memory_cache: dict = {}
        self._redis_url = redis_url or "redis://localhost:6379"
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed, using in-memory cache")
            return False

        try:
            self._redis = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
            return True
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory cache: {e}")
            self._redis = None
            self._connected = False
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self._redis and self._connected:
                value = await self._redis.get(f"lobinho:{key}")
                if value:
                    return json.loads(value)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = TTL_MEDIUM
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            serialized = json.dumps(value, default=str)

            if self._redis and self._connected:
                await self._redis.setex(
                    f"lobinho:{key}",
                    ttl,
                    serialized
                )
            else:
                self._memory_cache[key] = {
                    "value": value,
                    "expires": self._get_expiry(ttl)
                }
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self._redis and self._connected:
                await self._redis.delete(f"lobinho:{key}")
            else:
                self._memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        count = 0
        try:
            if self._redis and self._connected:
                keys = await self._redis.keys(f"lobinho:{pattern}")
                if keys:
                    count = await self._redis.delete(*keys)
            else:
                to_delete = [k for k in self._memory_cache if pattern.replace("*", "") in k]
                for k in to_delete:
                    del self._memory_cache[k]
                count = len(to_delete)
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
        return count

    def _get_expiry(self, ttl: int) -> float:
        """Get expiry timestamp."""
        import time
        return time.time() + ttl

    # ========================================================================
    # CACHING DECORATORS
    # ========================================================================

    def cached(self, ttl: int = TTL_MEDIUM, key_prefix: str = ""):
        """
        Decorator to cache function results.

        Usage:
            @cache.cached(ttl=300, key_prefix="odds")
            async def get_odds(match_id: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(key_prefix, func.__name__, args, kwargs)

                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await self.set(cache_key, result, ttl)

                return result
            return wrapper
        return decorator

    def _generate_key(
        self,
        prefix: str,
        func_name: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate unique cache key from function call."""
        key_parts = [prefix, func_name]

        # Add args
        for arg in args:
            if hasattr(arg, '__dict__'):
                key_parts.append(str(id(arg)))
            else:
                key_parts.append(str(arg))

        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)

        # Hash long keys
        if len(key_string) > 200:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"

        return key_string


# ============================================================================
# SPECIFIC CACHE KEYS
# ============================================================================

class CacheKeys:
    """Predefined cache keys for the system."""

    # Events and matches
    @staticmethod
    def upcoming_matches(league_id: Optional[int] = None) -> str:
        if league_id:
            return f"matches:upcoming:{league_id}"
        return "matches:upcoming:all"

    @staticmethod
    def live_matches() -> str:
        return "matches:live"

    @staticmethod
    def match_odds(match_id: int) -> str:
        return f"odds:match:{match_id}"

    # Teams
    @staticmethod
    def team_form(team_id: int) -> str:
        return f"team:form:{team_id}"

    @staticmethod
    def team_stats(team_id: int) -> str:
        return f"team:stats:{team_id}"

    # Predictions
    @staticmethod
    def match_prediction(match_id: int) -> str:
        return f"prediction:match:{match_id}"

    @staticmethod
    def value_bets() -> str:
        return "valuebets:current"

    # Dashboard
    @staticmethod
    def dashboard_data() -> str:
        return "dashboard:data"

    @staticmethod
    def statistics_daily() -> str:
        return "stats:daily"


# ============================================================================
# SINGLETON
# ============================================================================

_cache_instance: Optional[CacheService] = None


async def get_cache() -> CacheService:
    """Get or create CacheService singleton."""
    global _cache_instance
    if _cache_instance is None:
        from src.core.config import get_settings
        settings = get_settings()
        _cache_instance = CacheService(settings.redis_url)
        await _cache_instance.connect()
    return _cache_instance


# ============================================================================
# CACHE UTILS
# ============================================================================

async def invalidate_match_cache(match_id: int):
    """Invalidate all caches related to a match."""
    cache = await get_cache()
    await cache.delete(CacheKeys.match_odds(match_id))
    await cache.delete(CacheKeys.match_prediction(match_id))
    await cache.delete(CacheKeys.dashboard_data())


async def invalidate_team_cache(team_id: int):
    """Invalidate all caches related to a team."""
    cache = await get_cache()
    await cache.delete(CacheKeys.team_form(team_id))
    await cache.delete(CacheKeys.team_stats(team_id))


async def warm_cache():
    """Pre-populate cache with commonly accessed data."""
    logger.info("Warming up cache...")
    cache = await get_cache()

    # This would be called on startup to pre-load data
    # Implementation depends on what data is most frequently accessed

    logger.info("Cache warm-up complete")
