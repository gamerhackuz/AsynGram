from __future__ import annotations

import asyncio
import logging
from turtle import update
from typing import Any, Callable, List, Optional, Type

from .handler import HandlerRegistry
from .middleware import BaseMiddleware, MiddlewareChain
from .router import Router
from ..core.types import Update
from ..utils.exceptions import TelegramNetworkError
from asyngram.dispatcher import handler

logger = logging.getLogger("telegrampy.dispatcher")


class Dispatcher:
    """
    Updatelarni qabul qilib, to'g'ri handlerga yo'naltiradi.

    Polling va Webhook ikkalasini ham qo'llab-quvvatlaydi.
    Middleware chain orqali har bir update o'tadi.
    """

    def __init__(self, router: Router):
        self.router = router
        self._middleware = MiddlewareChain()
        self._running = False
        self._album_buffer: dict[str, list] = {}  # media group buffer
        self._album_tasks: dict[str, asyncio.Task] = {}

    # ─────────────────────────────────────────
    # Middleware
    # ─────────────────────────────────────────

    def use(self, middleware: BaseMiddleware) -> None:
        """
        Middleware qo'shish:
            dp.use(LoggingMiddleware())
            dp.use(ThrottlingMiddleware(rate=1.0))
        """
        self._middleware.add(middleware)
        logger.debug(f"Middleware qo'shildi: {type(middleware).__name__}")

    # ─────────────────────────────────────────
    # Update qayta ishlash
    # ─────────────────────────────────────────

    async def process_update(self, update: Update, bot: Any) -> None:
        """
        Bitta updateni to'liq qayta ishlaydi:
        1. Album buffering (media group)
        2. State inject
        3. Admin inject
        4. Middleware chain
        5. Handler topish va ishga tushirish
        """

        # Album (media group) ni buffer qilish
        msg = update.effective_message
        if msg and msg.media_group_id:
            await self._handle_album(update, bot)
            return

        # State va admin inject
        await self._inject_meta(update, bot)

        # Middleware + handler
        await self._middleware.process(update, bot, self._dispatch)

    async def _dispatch(self, update: Update, bot: Any) -> None:
        """Handlerni topib ishga tushiradi."""
        handler = await self.router.registry.find(update)

        if handler is None:
            logger.debug(f"[{update.event_type}] Mos handler topilmadi")
            return

        # Context yaratish
        from ..context.context import Context
        ctx = Context(update=update, bot=bot)

        logger.debug(f"[{update.event_type}] → {handler.name}")
        await handler.call(ctx)
        print("EVENT:", update.event_type)
        print("CALLBACK DATA:", update.callback_query.data if update.callback_query else None)
        handler = await self.router.registry.find(update)
        print("HANDLER:", handler)
        print("EVENT:", update.event_type)
        print("CALLBACK:", update.callback_query)
        print("REGISTRY:", self.router.registry._handlers)

    # ─────────────────────────────────────────
    # Meta inject (state, admin)
    # ─────────────────────────────────────────

    async def _inject_meta(self, update: Update, bot: Any) -> None:
        """State va admin ma'lumotlarini update ga inject qiladi."""

        user = update.effective_user
        chat = update.effective_chat

        if user and hasattr(bot, "_fsm_storage"):
            try:
                state = await bot._fsm_storage.get_state(user.id)
                update._current_state = state
            except Exception:
                update._current_state = None
        else:
            update._current_state = None

        # Admin tekshiruvi
        if user and chat and not chat.is_private:
            try:
                member = await bot.get_chat_member(chat.id, user.id)
                status = member.get("status", "")
                update._is_admin = status in ("creator", "administrator")
            except Exception:
                update._is_admin = False
        else:
            update._is_admin = False

    # ─────────────────────────────────────────
    # Album (Media Group) buffer
    # ─────────────────────────────────────────

    async def _handle_album(self, update: Update, bot: Any) -> None:
        """
        Media group xabarlarini buffer qilib, hammasini birga qayta ishlaydi.
        Telegram albumni alohida-alohida xabar sifatida yuboradi.
        Biz ularni 0.5s ichida to'plab, bitta update sifatida beramiz.
        """
        msg = update.effective_message
        group_id = msg.media_group_id

        if group_id not in self._album_buffer:
            self._album_buffer[group_id] = []

        self._album_buffer[group_id].append(update)

        # Oldingi task bo'lsa bekor qilamiz — yangi xabar keldi
        if group_id in self._album_tasks:
            self._album_tasks[group_id].cancel()

        # 0.5s kutib, keyin dispatch qilamiz
        task = asyncio.create_task(
            self._flush_album(group_id, bot)
        )
        self._album_tasks[group_id] = task

    async def _flush_album(self, group_id: str, bot: Any) -> None:
        """Album bufferini tozalab, bitta update sifatida dispatch qiladi."""
        await asyncio.sleep(0.5)

        updates = self._album_buffer.pop(group_id, [])
        self._album_tasks.pop(group_id, None)

        if not updates:
            return

        # Birinchi updatega media ro'yxatini inject qilamiz
        first_update = updates[0]
        first_update._album_messages = [u.effective_message for u in updates]

        await self._inject_meta(first_update, bot)
        await self._middleware.process(first_update, bot, self._dispatch)

    # ─────────────────────────────────────────
    # Polling
    # ─────────────────────────────────────────

    async def start_polling(
        self,
        bot: Any,
        timeout: int = 30,
        allowed_updates: Optional[List[str]] = None,
        drop_pending_updates: bool = False,
    ) -> None:
        """
        Long polling rejimida updatelarni qabul qiladi.

        bot.start_polling() — oddiy ishga tushirish
        """
        self._running = True
        offset = None

        # Webhook o'chiriladi
        await bot.delete_webhook(drop_pending_updates=drop_pending_updates)

        logger.info("Polling boshlandi ✓")

        while self._running:
            try:
                updates = await bot.get_updates(
                    offset=offset,
                    timeout=timeout,
                    allowed_updates=allowed_updates,
                )

                for update in updates:
                    offset = update.update_id + 1
                    asyncio.create_task(
                        self._safe_process(update, bot)
                    )

            except TelegramNetworkError as e:
                logger.error(f"Tarmoq xatosi: {e}. 5s kutilmoqda...")
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Polling xatosi: {e}", exc_info=True)
                await asyncio.sleep(1)

        logger.info("Polling to'xtatildi")

    async def stop_polling(self) -> None:
        self._running = False
        logger.info("Polling to'xtatilish so'raldi")

    async def _safe_process(self, update: Update, bot: Any) -> None:
        """Xatoni ushlagan holda updateni qayta ishlaydi."""
        try:
            await self.process_update(update, bot)
        except Exception as e:
            logger.error(
                f"Update #{update.update_id} qayta ishlashda xato: {e}",
                exc_info=True,
            )

    # ─────────────────────────────────────────
    # Webhook
    # ─────────────────────────────────────────

    async def feed_update(self, data: dict, bot: Any) -> None:
        """
        Webhook rejimida tashqaridan update qabul qiladi.
        Web framework (aiohttp, FastAPI) bu metodga raw JSON beradi.

        Misol (FastAPI):
            @app.post("/webhook")
            async def webhook(request: Request):
                data = await request.json()
                await dp.feed_update(data, bot)
        """
        try:
            update = Update(**data)
            await self._safe_process(update, bot)
        except Exception as e:
            logger.error(f"Webhook update parse xatosi: {e}", exc_info=True)
    
    