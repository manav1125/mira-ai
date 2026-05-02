import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

from core.services import redis
from core.utils.logger import logger


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class FixedWindowRateLimiter:
    def __init__(self, namespace: str, max_fallback_keys: int = 5000):
        self.namespace = namespace
        self._fallback: OrderedDict[str, tuple[int, float]] = OrderedDict()
        self._max_fallback_keys = max_fallback_keys

    def _fallback_check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        count, reset_at = self._fallback.get(key, (0, now + window_seconds))
        if now >= reset_at:
            count = 0
            reset_at = now + window_seconds

        count += 1
        self._fallback[key] = (count, reset_at)
        self._fallback.move_to_end(key)
        while len(self._fallback) > self._max_fallback_keys:
            self._fallback.popitem(last=False)

        retry_after = max(1, int(reset_at - now))
        return RateLimitResult(
            allowed=count <= limit,
            limit=limit,
            remaining=max(0, limit - count),
            retry_after_seconds=retry_after if count > limit else 0,
        )

    async def check(self, identity: str, limit: int, window_seconds: int) -> RateLimitResult:
        key = f"rate_limit:{self.namespace}:{identity}:{int(time.time() // window_seconds)}"
        try:
            count = await redis.incr(key, timeout=1.0)
            if count == 1:
                await redis.expire(key, window_seconds + 5, timeout=1.0)

            if count == 0:
                raise RuntimeError("Redis increment returned 0")

            retry_after = await redis.ttl(key, timeout=1.0)
            retry_after = retry_after if retry_after and retry_after > 0 else window_seconds
            return RateLimitResult(
                allowed=count <= limit,
                limit=limit,
                remaining=max(0, limit - count),
                retry_after_seconds=retry_after if count > limit else 0,
            )
        except Exception as exc:
            logger.warning(f"[RATE_LIMIT] Redis unavailable for {self.namespace}; using in-memory fallback: {exc}")
            return self._fallback_check(key, limit, window_seconds)


agent_start_rate_limiter = FixedWindowRateLimiter("agent_start")


async def check_agent_start_rate_limit(account_id: str, user_id: Optional[str] = None) -> RateLimitResult:
    limit = int(os.getenv("AGENT_START_RATE_LIMIT_PER_MINUTE", "30"))
    if limit <= 0:
        return RateLimitResult(allowed=True, limit=limit, remaining=0, retry_after_seconds=0)

    identity = account_id or user_id or "anonymous"
    return await agent_start_rate_limiter.check(identity=identity, limit=limit, window_seconds=60)
