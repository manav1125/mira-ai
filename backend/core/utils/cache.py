import json
from datetime import datetime, date
from typing import Any
from core.services.redis import get_client
from core.utils.logger import logger


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class _cache:
    async def get(self, key: str):
        cache_key = f"cache:{key}"
        try:
            redis = await get_client()
            result = await redis.get(cache_key)
            if result:
                return json.loads(result)
        except Exception as e:
            logger.debug(f"[CACHE] GET skipped for {cache_key}: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 15 * 60):
        cache_key = f"cache:{key}"
        try:
            redis = await get_client()
            await redis.set(cache_key, json.dumps(value, cls=DateTimeEncoder), ex=ttl)
        except Exception as e:
            logger.debug(f"[CACHE] SET skipped for {cache_key}: {e}")

    async def invalidate(self, key: str):
        cache_key = f"cache:{key}"
        try:
            redis = await get_client()
            await redis.delete(cache_key)
        except Exception as e:
            logger.debug(f"[CACHE] INVALIDATE skipped for {cache_key}: {e}")
    
    async def invalidate_multiple(self, keys: list[str]):
        """Invalidate multiple cache keys using batch delete."""
        try:
            from core.services.redis import delete_multiple
            prefixed_keys = [f"cache:{key}" for key in keys]
            await delete_multiple(prefixed_keys, timeout=5.0)
        except Exception as e:
            logger.debug(f"[CACHE] INVALIDATE_MULTIPLE skipped: {e}")


Cache = _cache()
