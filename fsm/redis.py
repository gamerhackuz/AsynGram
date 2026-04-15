from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from .storage import BaseStorage

logger = logging.getLogger("telegrampy.fsm.redis")


class RedisStorage(BaseStorage):
    """
    Redis asosida persistent FSM storage.
    Bot o'chsa ham state saqlanib qoladi.
    Multi-instance botlarda ham ishlaydi.

    Ishlatish:
        from telegrampy.fsm import RedisStorage

        storage = await RedisStorage.create("redis://localhost:6379")
        bot = Bot("TOKEN", storage=storage)

    Yoki:
        storage = RedisStorage.from_url("redis://localhost:6379")
        bot = Bot("TOKEN", storage=storage)
    """

    def __init__(self, redis: Any, prefix: str = "telegrampy:fsm"):
        self._redis = redis
        self._prefix = prefix

    # ─────────────────────────────────────────
    # Yaratish
    # ─────────────────────────────────────────

    @classmethod
    async def create(
        cls,
        url: str = "redis://localhost:6379",
        prefix: str = "telegrampy:fsm",
        **kwargs,
    ) -> "RedisStorage":
        """
        Async yaratish:
            storage = await RedisStorage.create("redis://localhost:6379")
        """
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError("Redis kerak: pip install redis")

        client = await aioredis.from_url(url, decode_responses=True, **kwargs)
        logger.info(f"RedisStorage ulandi: {url}")
        return cls(redis=client, prefix=prefix)

    @classmethod
    def from_url(
        cls,
        url: str = "redis://localhost:6379",
        prefix: str = "telegrampy:fsm",
        **kwargs,
    ) -> "RedisStorage":
        """
        Sinxron yaratish (bot ishga tushganda ulanadi):
            storage = RedisStorage.from_url("redis://localhost:6379")
        """
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError("Redis kerak: pip install redis")

        client = aioredis.from_url(url, decode_responses=True, **kwargs)
        return cls(redis=client, prefix=prefix)

    # ─────────────────────────────────────────
    # Key generatsiya
    # ─────────────────────────────────────────

    def _state_key(self, user_id: int) -> str:
        return f"{self._prefix}:{user_id}:state"

    def _data_key(self, user_id: int) -> str:
        return f"{self._prefix}:{user_id}:data"

    # ─────────────────────────────────────────
    # BaseStorage interfeysi
    # ─────────────────────────────────────────

    async def get_state(self, user_id: int) -> Optional[str]:
        value = await self._redis.get(self._state_key(user_id))
        return value

    async def set_state(
        self,
        user_id: int,
        state: str,
        ttl: Optional[int] = None,
    ) -> None:
        """
        State saqlaydi.
        ttl — soniyada muddat (None = abadiy)
        """
        key = self._state_key(user_id)
        if ttl:
            await self._redis.setex(key, ttl, state)
        else:
            await self._redis.set(key, state)

    async def get_data(self, user_id: int) -> Dict[str, Any]:
        raw = await self._redis.get(self._data_key(user_id))
        if raw is None:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Data parse xatosi: user={user_id}")
            return {}

    async def update_data(self, user_id: int, data: Dict[str, Any]) -> None:
        current = await self.get_data(user_id)
        current.update(data)
        await self._redis.set(
            self._data_key(user_id),
            json.dumps(current, ensure_ascii=False),
        )

    async def clear(self, user_id: int) -> None:
        await self._redis.delete(
            self._state_key(user_id),
            self._data_key(user_id),
        )

    # ─────────────────────────────────────────
    # Qo'shimcha metodlar
    # ─────────────────────────────────────────

    async def set_ttl(self, user_id: int, seconds: int) -> None:
        """State va dataga muddat belgilaydi."""
        await self._redis.expire(self._state_key(user_id), seconds)
        await self._redis.expire(self._data_key(user_id), seconds)

    async def all_users(self) -> list[int]:
        """State mavjud barcha userlarni qaytaradi."""
        pattern = f"{self._prefix}:*:state"
        keys = await self._redis.keys(pattern)
        user_ids = []
        for key in keys:
            parts = key.split(":")
            try:
                user_ids.append(int(parts[-2]))
            except (IndexError, ValueError):
                pass
        return user_ids

    async def close(self) -> None:
        await self._redis.aclose()
        logger.info("RedisStorage ulanishi yopildi")

    def __repr__(self) -> str:
        return f"RedisStorage(prefix={self._prefix!r})"