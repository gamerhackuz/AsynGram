from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from ..core.types import Update

logger = logging.getLogger("telegrampy.middleware")

# Handler tipini belgilash
NextHandler = Callable[[Update, Any], Any]


# ─────────────────────────────────────────
# Base
# ─────────────────────────────────────────

class BaseMiddleware(ABC):
    """
    Barcha middlewarelar shu klassdan meros oladi.

    Misol:
        class MyMiddleware(BaseMiddleware):
            async def __call__(self, update, bot, next):
                print("Updatedan oldin")
                await next(update, bot)
                print("Updatedan keyin")
    """

    @abstractmethod
    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        ...


# ─────────────────────────────────────────
# Middleware Chain
# ─────────────────────────────────────────

class MiddlewareChain:
    """
    Middlewarelarni zanjir sifatida ishga tushiradi.

    dp.use(LoggingMiddleware())
    dp.use(ThrottlingMiddleware())

    Ishga tushish tartibi: LIFO (oxirgi qo'shilgan — birinchi ishlaydi)
    """

    def __init__(self):
        self._middlewares: list[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware) -> None:
        self._middlewares.append(middleware)

    async def process(self, update: Update, bot: Any, final: NextHandler) -> None:
        """Zanjirni ishga tushiradi."""

        async def build_chain(index: int) -> None:
            if index >= len(self._middlewares):
                await final(update, bot)
                return

            middleware = self._middlewares[index]

            async def next_fn(u: Update, b: Any) -> None:
                await build_chain(index + 1)

            await middleware(update, bot, next_fn)

        await build_chain(0)

    def __len__(self) -> int:
        return len(self._middlewares)


# ─────────────────────────────────────────
# Tayyor middlewarelar
# ─────────────────────────────────────────

class LoggingMiddleware(BaseMiddleware):
    """
    Har bir updateni loglaydi — vaqt, foydalanuvchi, event turi.

    dp.use(LoggingMiddleware())
    dp.use(LoggingMiddleware(level=logging.DEBUG))
    """

    def __init__(self, level: int = logging.INFO):
        self.level = level

    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        user = update.effective_user
        chat = update.effective_chat
        start = time.monotonic()

        user_info = f"@{user.username}" if (user and user.username) else (f"id={user.id}" if user else "?")
        chat_info = f"chat={chat.id}" if chat else ""

        logger.log(self.level, f"▶ [{update.event_type}] {user_info} {chat_info}")

        await next(update, bot)

        elapsed = (time.monotonic() - start) * 1000
        logger.log(self.level, f"✓ [{update.event_type}] {user_info} — {elapsed:.1f}ms")


class ThrottlingMiddleware(BaseMiddleware):
    """
    Foydalanuvchi juda tez xabar yuborganida bloklaydi.

    dp.use(ThrottlingMiddleware(rate=1.0))  # 1 soniyada 1 ta
    dp.use(ThrottlingMiddleware(rate=0.5))  # 0.5 soniyada 1 ta
    """

    def __init__(self, rate: float = 1.0):
        self.rate = rate
        self._last_seen: Dict[int, float] = {}

    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        user = update.effective_user
        if not user:
            await next(update, bot)
            return

        now = time.monotonic()
        last = self._last_seen.get(user.id, 0)

        if now - last < self.rate:
            logger.debug(f"Throttle: user {user.id} juda tez yubormoqda")
            return  # Updateni o'tkazib yuboradi — xato yo'q, jim o'tadi

        self._last_seen[user.id] = now
        await next(update, bot)


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Handler xatolarini ushlaydi va foydalanuvchiga xabar beradi.

    dp.use(ErrorHandlerMiddleware())
    dp.use(ErrorHandlerMiddleware(message="Xato yuz berdi, qayta urinib ko'ring"))
    """

    def __init__(self, message: str = "⚠️ Xato yuz berdi. Iltimos, qayta urinib ko'ring."):
        self.message = message

    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        try:
            await next(update, bot)
        except Exception as e:
            logger.error(f"Handler xatosi: {e}", exc_info=True)
            chat = update.effective_chat
            if chat:
                try:
                    await bot.send_message(chat.id, self.message)
                except Exception:
                    pass


class UserDataMiddleware(BaseMiddleware):
    """
    Har bir updateda foydalanuvchi ma'lumotlarini inject qiladi.
    DI tizimi bilan ishlaydi — ctx.user_data orqali olinadi.

    dp.use(UserDataMiddleware(db=my_db))
    """

    def __init__(self, db: Any):
        self.db = db

    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        user = update.effective_user
        if user and hasattr(self.db, "get_user"):
            try:
                update._user_data = await self.db.get_user(user.id)
            except Exception:
                update._user_data = None
        await next(update, bot)


class ChatMemberMiddleware(BaseMiddleware):
    """
    Foydalanuvchining belgilangan kanallarga a'zoligini tekshiradi.

    dp.use(ChatMemberMiddleware(bot, required_chats=[-1001234567890]))
    """

    def __init__(self, required_chats: list[int], on_fail_message: Optional[str] = None):
        self.required_chats = required_chats
        self.on_fail_message = on_fail_message or "❌ Davom etish uchun kanalga obuna bo'ling."

    async def __call__(self, update: Update, bot: Any, next: NextHandler) -> None:
        user = update.effective_user
        chat = update.effective_chat

        if not user or not chat or not chat.is_private:
            await next(update, bot)
            return

        for channel_id in self.required_chats:
            try:
                member = await bot.get_chat_member(channel_id, user.id)
                status = member.get("status", "left")
                if status in ("left", "kicked"):
                    await bot.send_message(chat.id, self.on_fail_message)
                    return
            except Exception:
                pass

        await next(update, bot)