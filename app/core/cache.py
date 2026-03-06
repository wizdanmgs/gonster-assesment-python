import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import structlog
from redis.asyncio import Redis
from redis.exceptions import ConnectionError

from app.core.config import settings

logger = structlog.get_logger(__name__)


class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        pass

    @abstractmethod
    async def setex(self, key: str, time: int, value: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class RedisCacheBackend(CacheBackend):
    def __init__(self, url: str):
        self._url = url
        self._redis = Redis.from_url(url, decode_responses=True)

    async def _execute_with_retry(self, func, *args, **kwargs):
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except ConnectionError as e:
                logger.warning(
                    "Redis connection lost, initiating retry",
                    redis_url=self._url,
                    attempt=attempt,
                    max_retries=max_retries,
                    error=f"{type(e).__name__}: {str(e)}",
                )
                if attempt == max_retries:
                    raise
                await asyncio.sleep(1)

    async def get(self, key: str) -> Optional[str]:
        return await self._execute_with_retry(self._redis.get, key)

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        if not keys:
            return []
        return await self._execute_with_retry(self._redis.mget, keys)

    async def setex(self, key: str, time: int, value: str) -> None:
        await self._execute_with_retry(self._redis.setex, key, time, value)

    async def delete(self, key: str) -> None:
        await self._execute_with_retry(self._redis.delete, key)

    async def close(self) -> None:
        await self._execute_with_retry(self._redis.aclose)


# Global cache instance
cache_backend: Optional[CacheBackend] = None


async def init_cache() -> None:
    global cache_backend
    if settings.CACHE_DB_ENGINE == "redis":
        cache_backend = RedisCacheBackend(settings.CACHE_DB_URL)
    # Other Cache DB Here


async def close_cache() -> None:
    if cache_backend:
        await cache_backend.close()


def get_cache() -> Optional[CacheBackend]:
    return cache_backend
