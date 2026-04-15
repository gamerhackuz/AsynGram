from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("telegrampy.contrib.throttling")


class ThrottleStorage:
    """In-memory throttle storage."""

    def __init__(self):
        self._data: Dict[str, Dict[str, float]] = {}

    def get_last(self, user_id: int, key: str) -> float:
        return self._data.get(str(user_id), {}).get(key, 0.0)

    def set_last(self, user_id: int, key: str, ts: float) -> None:
        uid = str(user_id)
        if uid not in self._data:
            self._data[uid] = {}
        self._data[uid][key] = ts

    def clear(self, user_id: int) -> None:
        self._data.pop(str(user_id), None)


class Throttling:
    """
    Kengaytirilgan rate limiting tizimi.
    ThrottlingMiddleware dan farqli — handler darajasida ishlaydi.

    Ishlatish:
        throttle = Throttling()
        bot.provide(throttle=throttle)

        @bot.on.message.command("start")
        async def start(ctx, throttle):
            if await throttle.check(ctx.user.id, "start", rate=5.0):
                await ctx.answer("5 soniyada bir marta!")
                return
            await ctx.answer("Salom!")

    Yoki dekorator sifatida:
        @bot.on.message.command("pay")
        @throttle.limit(rate=10.0, key="pay", message="10s kuting")
        async def pay(ctx):
            ...
    """

    def __init__(self, storage: Optional[ThrottleStorage] = None):
        self._storage = storage or ThrottleStorage()

    async def check(
        self,
        user_id: int,
        key: str = "default",
        rate: float = 1.0,
    ) -> bool:
        """
        True qaytarsa — limit urilgan (handler to'xtatilishi kerak).
        False qaytarsa — davom etish mumkin.
        """
        now = time.monotonic()
        last = self._storage.get_last(user_id, key)

        if now - last < rate:
            logger.debug(f"Throttle: user={user_id} key={key} ({now - last:.2f}s < {rate}s)")
            return True

        self._storage.set_last(user_id, key, now)
        return False

    async def remaining(self, user_id: int, key: str = "default", rate: float = 1.0) -> float:
        """Kutish vaqtini qaytaradi (soniyada)."""
        now = time.monotonic()
        last = self._storage.get_last(user_id, key)
        wait = rate - (now - last)
        return max(0.0, wait)

    def limit(
        self,
        rate: float = 1.0,
        key: Optional[str] = None,
        message: Optional[str] = None,
        alert: bool = False,
    ) -> Callable:
        """
        Handler uchun dekorator:

        @bot.on.message.command("flood")
        @throttle.limit(rate=5.0, message="⏳ 5 soniya kuting!")
        async def flood(ctx):
            await ctx.answer("OK")
        """
        def decorator(func: Callable) -> Callable:
            throttle_key = key or func.__name__

            async def wrapper(ctx: Any) -> Any:
                user_id = ctx.from_id
                if not user_id:
                    return await func(ctx)

                throttled = await self.check(user_id, throttle_key, rate)

                if throttled:
                    wait = await self.remaining(user_id, throttle_key, rate)
                    warn = message or f"⏳ {wait:.1f}s kuting."

                    if alert and ctx.callback:
                        await ctx.alert(warn)
                    elif message:
                        await ctx.answer(warn)
                    return

                return await func(ctx)

            wrapper.__name__ = func.__name__
            wrapper.__wrapped__ = func
            return wrapper

        return decorator

    def reset(self, user_id: int) -> None:
        """Foydalanuvchi limitini tiklaydi."""
        self._storage.clear(user_id)


class CooldownManager:
    """
    Bir martalik cooldown — masalan, kunlik bonus uchun.

    cooldown = CooldownManager(seconds=86400)  # 24 soat

    if await cooldown.is_ready(ctx.user.id):
        await give_bonus(ctx)
        await cooldown.set(ctx.user.id)
    else:
        left = await cooldown.time_left(ctx.user.id)
        await ctx.answer(f"Bonus {left}dan keyin tayyor!")
    """

    def __init__(self, seconds: float):
        self.seconds = seconds
        self._storage = ThrottleStorage()

    async def is_ready(self, user_id: int, key: str = "cooldown") -> bool:
        now = time.monotonic()
        last = self._storage.get_last(user_id, key)
        return now - last >= self.seconds

    async def set(self, user_id: int, key: str = "cooldown") -> None:
        self._storage.set_last(user_id, key, time.monotonic())

    async def time_left(self, user_id: int, key: str = "cooldown") -> float:
        now = time.monotonic()
        last = self._storage.get_last(user_id, key)
        return max(0.0, self.seconds - (now - last))

    async def reset(self, user_id: int, key: str = "cooldown") -> None:
        self._storage.set_last(user_id, key, 0.0)