from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, List, Optional

from .filters import BaseFilter
from ..core.types import Update

logger = logging.getLogger("telegrampy.handler")


class Handler:
    """
    Bitta handler = funksiya + filterlar ro'yxati.

    Dispatcher bu ro'yxatni ko'rib chiqib, birinchi mosini ishga tushiradi.
    """

    def __init__(
        self,
        func: Callable,
        filters: List[BaseFilter],
        priority: int = 0,
    ):
        self.func = func
        self.filters = filters
        self.priority = priority
        self.name = func.__name__

    async def check(self, update: Update) -> bool:
        """Barcha filterlar o'tsa True qaytaradi."""
        for f in self.filters:
            try:
                if not await f.check(update):
                    return False
            except Exception as e:
                logger.error(f"[{self.name}] Filter xatosi ({type(f).__name__}): {e}")
                return False
        return True

    async def call(self, context: Any) -> Any:
        """Handlerni ishga tushiradi."""
        try:
            result = self.func(context)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            logger.error(f"[{self.name}] Handler xatosi: {e}", exc_info=True)
            raise

    def __repr__(self) -> str:
        return (
            f"Handler(name={self.name!r}, "
            f"filters={[type(f).__name__ for f in self.filters]}, "
            f"priority={self.priority})"
        )


class HandlerRegistry:
    """
    Barcha handlerlar shu registryda saqlanadi.
    Dispatcher bu registrydan foydalanadi.
    """

    def __init__(self):
        self._handlers: List[Handler] = []

    def register(
        self,
        func: Callable,
        filters: List[BaseFilter],
        priority: int = 0,
    ) -> Handler:
        handler = Handler(func, filters, priority)
        self._handlers.append(handler)
        # Priority bo'yicha saralash — katta priority = birinchi tekshiriladi
        self._handlers.sort(key=lambda h: h.priority, reverse=True)
        logger.debug(f"Handler ro'yxatga olindi: {handler}")
        return handler

    async def find(self, update: Update) -> Optional[Handler]:
        """Updatega mos birinchi handlerni topadi."""
        for handler in self._handlers:
            if await handler.check(update):
                return handler
        return None

    async def find_all(self, update: Update) -> List[Handler]:
        """Updatega mos barcha handlerlarni topadi."""
        result = []
        for handler in self._handlers:
            if await handler.check(update):
                result.append(handler)
        return result

    def remove(self, func: Callable) -> bool:
        before = len(self._handlers)
        self._handlers = [h for h in self._handlers if h.func is not func]
        return len(self._handlers) < before

    def clear(self) -> None:
        self._handlers.clear()

    def __len__(self) -> int:
        return len(self._handlers)

    def __repr__(self) -> str:
        return f"HandlerRegistry({len(self._handlers)} handlers)"