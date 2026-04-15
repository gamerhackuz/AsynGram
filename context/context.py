from __future__ import annotations

import re
from typing import Any, List, Optional, Union

from ..core.types import (
    Update, Message, User, Chat,
    CallbackQuery, InlineQuery,
)
from ..core.methods import FileInput, KeyboardInput


class Context:
    """
    Universal context obyekti — handler ichida hamma narsa ctx orqali.

    Dasturchi bot, types, FSMContext kabi narsalarni import qilmaydi.
    Faqat bitta ctx yetarli.
    """

    def __init__(self, update: Update, bot: Any):
        self._update = update
        self._bot = bot

        # Tez-tez ishlatiladiganlar
        self.user: Optional[User] = update.effective_user
        self.chat: Optional[Chat] = update.effective_chat
        self.message: Optional[Message] = update.effective_message
        self.callback: Optional[CallbackQuery] = update.callback_query
        self.inline: Optional[InlineQuery] = update.inline_query

        # Regex match — RegexFilter tomonidan yoziladi
        self.match: Optional[re.Match] = getattr(update, "_regex_match", None)

        # Album (media group) — AlbumFilter + Dispatcher tomonidan
        self.media: Optional[List[Message]] = getattr(update, "_album_messages", None)

        # State — Dispatcher tomonidan inject qilinadi
        self._current_state: Optional[str] = getattr(update, "_current_state", None)

        # User data — UserDataMiddleware tomonidan inject qilinadi
        self.user_data: Any = getattr(update, "_user_data", None)

        # Admin tekshiruvi
        self.is_admin: bool = getattr(update, "_is_admin", False)

        # Lazy fluent builder — import circular muammosidan saqlanish uchun
        self._fluent_class = None

    # ─────────────────────────────────────────
    # Asosiy shortcuts
    # ─────────────────────────────────────────

    @property
    def text(self) -> Optional[str]:
        """Xabar matni yoki caption."""
        if self.message:
            return self.message.text or self.message.caption
        return None

    @property
    def data(self) -> Optional[str]:
        """Callback data."""
        return self.callback.data if self.callback else None

    @property
    def args(self) -> str:
        """Komanda argumentlari: /start arg1 arg2 → 'arg1 arg2'"""
        return self.message.args if self.message else ""

    @property
    def from_id(self) -> Optional[int]:
        return self.user.id if self.user else None

    @property
    def chat_id(self) -> Optional[int]:
        return self.chat.id if self.chat else None

    @property
    def message_id(self) -> Optional[int]:
        # callback da message_id callback.message dan olinishi kerak!
        if self.callback and self.callback.message:
            return self.callback.message.message_id
        return self.message.message_id if self.message else None
    @property
    
    def state(self) -> "StateProxy":
        """FSM state boshqaruvi: await ctx.state.set('waiting_name')"""
        return StateProxy(
            user_id=self.from_id,
            chat_id=self.chat_id,
            bot=self._bot,
        )

    @property
    def btn(self) -> "ButtonFactory":
        """Tezkor tugma yaratuvchi: ctx.btn.callback('Bosing', 'cb_data')"""
        return ButtonFactory()

    # ─────────────────────────────────────────
    # Javob berish — Fluent MessageBuilder qaytaradi
    # ─────────────────────────────────────────

    def answer(self, text: str, **kwargs) -> "MessageBuilder":
        """
        Xabarga javob beradi (reply emas, oddiy xabar).

        await ctx.answer("Salom!")
        await ctx.answer("Menyu:").inline_row(ctx.btn.callback("A", "a"))
        """
        from .fluent import MessageBuilder
        return MessageBuilder(
            bot=self._bot,
            chat_id=self.chat_id,
            text=text,
            **kwargs,
        )

    def reply(self, text: str, **kwargs) -> "MessageBuilder":
        """
        Xabarga reply (quote) bilan javob beradi.

        await ctx.reply("Javob!")
        """
        from .fluent import MessageBuilder
        return MessageBuilder(
            bot=self._bot,
            chat_id=self.chat_id,
            text=text,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    def edit(self, text: str, **kwargs) -> "MessageBuilder":
        """
        Xabarni tahrirlaydi (callback handler uchun).

        await ctx.edit("Yangi matn")
        await ctx.edit("Yangi matn").inline_row(...)
        """
        from .fluent import MessageBuilder
        return MessageBuilder(
            bot=self._bot,
            chat_id=self.chat_id,
            text=text,
            message_id=self.message_id,
            mode="edit",
            **kwargs,
        )

    # ─────────────────────────────────────────
    # Callback query metodlari
    # ─────────────────────────────────────────

    async def alert(self, text: str, show_alert: bool = True) -> None:
        """
        Callback queryga popup alert ko'rsatadi.

        await ctx.alert("Buyurtma tasdiqlandi!")
        """
        if not self.callback:
            return
        await self._bot.answer_callback_query(
            callback_query_id=self.callback.id,
            text=text,
            show_alert=show_alert,
        )

    async def notify(self, text: str) -> None:
        """
        Callback queryga toast (qisqa) xabar ko'rsatadi.

        await ctx.notify("✓ Saqlandi")
        """
        if not self.callback:
            return
        await self._bot.answer_callback_query(
            callback_query_id=self.callback.id,
            text=text,
            show_alert=False,
        )

    # ─────────────────────────────────────────
    # Xabar o'chirish / pin
    # ─────────────────────────────────────────

    async def delete(self, message_id: Optional[int] = None) -> bool:
        """
        Xabarni o'chiradi.

        await ctx.delete()               — joriy xabarni
        await ctx.delete(message_id=42)  — aniq xabarni
        """
        mid = message_id or self.message_id
        if not self.chat_id or not mid:
            return False
        return await self._bot.delete_message(self.chat_id, mid)

    async def pin(self, disable_notification: bool = False) -> bool:
        """Joriy xabarni pin qiladi."""
        if not self.chat_id or not self.message_id:
            return False
        return await self._bot.pin_message(
            self.chat_id, self.message_id, disable_notification
        )

    # ─────────────────────────────────────────
    # Media yuborish shortcutlari
    # ─────────────────────────────────────────

    async def send_photo(self, photo: FileInput, caption: str = None, **kwargs) -> Message:
        return await self._bot.send_photo(self.chat_id, photo, caption=caption, **kwargs)

    async def send_video(self, video: FileInput, caption: str = None, **kwargs) -> Message:
        return await self._bot.send_video(self.chat_id, video, caption=caption, **kwargs)

    async def send_document(self, document: FileInput, caption: str = None, **kwargs) -> Message:
        return await self._bot.send_document(self.chat_id, document, caption=caption, **kwargs)

    async def send_audio(self, audio: FileInput, caption: str = None, **kwargs) -> Message:
        return await self._bot.send_audio(self.chat_id, audio, caption=caption, **kwargs)

    async def send_voice(self, voice: FileInput, **kwargs) -> Message:
        return await self._bot.send_voice(self.chat_id, voice, **kwargs)

    async def send_album(
        self,
        files: List[FileInput],
        media_type: str = "photo",
        captions: Optional[List[str]] = None,
    ) -> List[Message]:
        """
        Album yuboradi.

        await ctx.send_album([photo1, photo2, photo3])
        """
        return await self._bot.send_media_group(
            self.chat_id, files, media_type=media_type, captions=captions
        )

    async def typing(self) -> None:
        """'Yozmoqda...' ko'rsatadi."""
        await self._bot.send_chat_action(self.chat_id, "typing")

    async def upload_photo(self) -> None:
        """'Rasm yuklayapti...' ko'rsatadi."""
        await self._bot.send_chat_action(self.chat_id, "upload_photo")

    # ─────────────────────────────────────────
    # Forward
    # ─────────────────────────────────────────

    async def forward_to(self, to_chat_id: Union[int, str]) -> Message:
        """Joriy xabarni boshqa chatga forward qiladi."""
        return await self._bot.forward_message(
            chat_id=to_chat_id,
            from_chat_id=self.chat_id,
            message_id=self.message_id,
        )

    # ─────────────────────────────────────────
    # Raw bot access
    # ─────────────────────────────────────────

    @property
    def bot(self) -> Any:
        """To'g'ridan-to'g'ri bot metodlariga kirish."""
        return self._bot

    def __repr__(self) -> str:
        return (
            f"Context("
            f"event={self._update.event_type!r}, "
            f"user={self.from_id}, "
            f"chat={self.chat_id})"
        )


# ─────────────────────────────────────────
# StateProxy — ctx.state uchun
# ─────────────────────────────────────────

class StateProxy:
    """
    FSM state boshqaruvi ctx.state orqali.

    await ctx.state.set("waiting_name")
    await ctx.state.get()
    await ctx.state.finish()
    await ctx.state.update(name="Ali")
    data = await ctx.state.get_data()
    """

    def __init__(self, user_id: int, chat_id: int, bot: Any):
        self._user_id = user_id
        self._chat_id = chat_id
        self._bot = bot

    @property
    def _storage(self):
        return getattr(self._bot, "_fsm_storage", None)

    async def set(self, state: str) -> None:
        if self._storage:
            await self._storage.set_state(self._user_id, state)

    async def get(self) -> Optional[str]:
        if self._storage:
            return await self._storage.get_state(self._user_id)
        return None

    async def finish(self) -> None:
        if self._storage:
            await self._storage.clear(self._user_id)

    async def update(self, **data) -> None:
        """State data ga qo'shimcha ma'lumot saqlash."""
        if self._storage:
            await self._storage.update_data(self._user_id, data)

    async def get_data(self) -> dict:
        """Saqlangan barcha state datani olish."""
        if self._storage:
            return await self._storage.get_data(self._user_id) or {}
        return {}


# ─────────────────────────────────────────
# ButtonFactory — ctx.btn uchun
# ─────────────────────────────────────────

class ButtonFactory:
    """
    Tezkor tugma yaratuvchi.

    ctx.btn.callback("Bosing", "my_data")
    ctx.btn.url("Sayt", "https://example.com")
    ctx.btn.web_app("App", "https://app.example.com")
    """

    def callback(self, text: str, data: str) -> dict:
        return {"text": text, "callback_data": data}

    def url(self, text: str, url: str) -> dict:
        return {"text": text, "url": url}

    def web_app(self, text: str, url: str) -> dict:
        return {"text": text, "web_app": {"url": url}}

    def switch_inline(self, text: str, query: str = "") -> dict:
        return {"text": text, "switch_inline_query": query}

    def switch_inline_current(self, text: str, query: str = "") -> dict:
        return {"text": text, "switch_inline_query_current_chat": query}