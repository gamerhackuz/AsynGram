from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Pattern, Union

from ..core.types import Update, Message, CallbackQuery


# ─────────────────────────────────────────
# Base
# ─────────────────────────────────────────

class BaseFilter(ABC):
    """Barcha filterlar shu klassdan meros oladi."""

    @abstractmethod
    async def check(self, update: Update) -> bool:
        """True qaytarsa — handler ishga tushadi."""
        ...

    def __and__(self, other: "BaseFilter") -> "AndFilter":
        return AndFilter(self, other)

    def __or__(self, other: "BaseFilter") -> "OrFilter":
        return OrFilter(self, other)

    def __invert__(self) -> "NotFilter":
        return NotFilter(self)


# ─────────────────────────────────────────
# Kombinatsiya filtrlari
# ─────────────────────────────────────────

class AndFilter(BaseFilter):
    def __init__(self, *filters: BaseFilter):
        self.filters = filters

    async def check(self, update: Update) -> bool:
        for f in self.filters:
            if not await f.check(update):
                return False
        return True


class OrFilter(BaseFilter):
    def __init__(self, *filters: BaseFilter):
        self.filters = filters

    async def check(self, update: Update) -> bool:
        for f in self.filters:
            if await f.check(update):
                return True
        return False


class NotFilter(BaseFilter):
    def __init__(self, filter: BaseFilter):
        self.filter = filter

    async def check(self, update: Update) -> bool:
        return not await self.filter.check(update)


class LambdaFilter(BaseFilter):
    """Tezkor custom filter: LambdaFilter(lambda u: u.effective_user.is_premium)"""

    def __init__(self, func: Callable):
        self.func = func

    async def check(self, update: Update) -> bool:
        result = self.func(update)
        if hasattr(result, "__await__"):
            return await result
        return bool(result)


# ─────────────────────────────────────────
# Update turi filtrlari
# ─────────────────────────────────────────

class MessageFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        return update.message is not None


class EditedMessageFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        return update.edited_message is not None


class CallbackFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        
        return update.callback_query is not None


class InlineQueryFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        return update.inline_query is not None


class PollFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        return update.poll is not None


class ChatJoinRequestFilter(BaseFilter):
    async def check(self, update: Update) -> bool:
        return update.chat_join_request is not None


# ─────────────────────────────────────────
# Chat turi filtrlari
# ─────────────────────────────────────────

class ChatTypeFilter(BaseFilter):
    def __init__(self, *chat_types: str):
        self.chat_types = set(chat_types)

    async def check(self, update: Update) -> bool:
        chat = update.effective_chat
        return chat is not None and chat.type in self.chat_types


# Tayyor instancelar — .private, .group, .channel sifatida ishlatiladi
PrivateFilter    = ChatTypeFilter("private")
GroupFilter      = ChatTypeFilter("group", "supergroup")
SupergroupFilter = ChatTypeFilter("supergroup")
ChannelFilter    = ChatTypeFilter("channel")


# ─────────────────────────────────────────
# Kontent turi filtrlari
# ─────────────────────────────────────────

class ContentTypeFilter(BaseFilter):
    def __init__(self, *content_types: str):
        self.content_types = set(content_types)

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        return msg is not None and msg.content_type in self.content_types


# Tayyor instancelar
TextFilter      = ContentTypeFilter("text")
PhotoFilter     = ContentTypeFilter("photo")
VideoFilter     = ContentTypeFilter("video")
AudioFilter     = ContentTypeFilter("audio")
DocumentFilter  = ContentTypeFilter("document")
VoiceFilter     = ContentTypeFilter("voice")
StickerFilter   = ContentTypeFilter("sticker")
LocationFilter  = ContentTypeFilter("location")
ContactFilter   = ContentTypeFilter("contact")


# ─────────────────────────────────────────
# Komanda filtri
# ─────────────────────────────────────────

class CommandFilter(BaseFilter):
    """
    @bot.on.message.command("start")
    @bot.on.message.command("start", "help", "menu")  # bir nechta
    """

    def __init__(self, *commands: str):
        self.commands = {cmd.lstrip("/").lower() for cmd in commands}

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        if not msg or not msg.is_command:
            return False
        return msg.command.lower() in self.commands


# ─────────────────────────────────────────
# Regex filtri
# ─────────────────────────────────────────

class RegexFilter(BaseFilter):
    r"""
    @bot.on.callback.data_regex(r'item_(\\d+)')
    ctx.match — regex natijasini saqlaydi
    """

    def __init__(self, pattern: Union[str, Pattern]):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self._match: Optional[re.Match] = None

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        if not msg:
            return False
        text = msg.text or msg.caption or ""
        match = self.pattern.search(text)
        if match:
            # match ni update ga yozib qo'yamiz — ctx.match orqali olinadi
            update._regex_match = match
            return True
        return False


# ─────────────────────────────────────────
# Callback Data filtrlari
# ─────────────────────────────────────────

class CallbackDataFilter(BaseFilter):
    """Aniq callback data: @bot.on.callback.data("delete")"""

    def __init__(self, *values: str):
        self.values = set(values)

    async def check(self, update: Update) -> bool:
        cb = update.callback_query
        return cb is not None and cb.data in self.values


class CallbackDataStartFilter(BaseFilter):
    """Prefix bilan: @bot.on.callback.data_start("order_")"""

    def __init__(self, prefix: str):
        self.prefix = prefix

    async def check(self, update: Update) -> bool:
        cb = update.callback_query
        return cb is not None and cb.data is not None and cb.data.startswith(self.prefix)


class CallbackDataRegexFilter(BaseFilter):
    """Regex bilan: @bot.on.callback.data_regex(r"item_(\d+)")"""

    def __init__(self, pattern: Union[str, Pattern]):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern

    async def check(self, update: Update) -> bool:
        cb = update.callback_query
        if not cb or not cb.data:
            return False
        match = self.pattern.search(cb.data)
        if match:
            update._regex_match = match
            return True
        return False


# ─────────────────────────────────────────
# State filtri (FSM)
# ─────────────────────────────────────────

class StateFilter(BaseFilter):
    """
    @bot.on.message.state("waiting_name")
    @bot.on.message.state("*")  — istalgan state
    """

    def __init__(self, *states: str):
        self.states = set(states)
        self.any = "*" in states

    async def check(self, update: Update) -> bool:
        # State storage dan olinadi — dispatcher inject qiladi
        current_state = getattr(update, "_current_state", None)
        if self.any:
            return current_state is not None
        return current_state in self.states


# ─────────────────────────────────────────
# Foydalanuvchi filtrlari
# ─────────────────────────────────────────

class UserIdFilter(BaseFilter):
    """Faqat belgilangan user IDlar uchun."""

    def __init__(self, *user_ids: int):
        self.user_ids = set(user_ids)

    async def check(self, update: Update) -> bool:
        user = update.effective_user
        return user is not None and user.id in self.user_ids


class AdminFilter(BaseFilter):
    """
    Faqat adminlar uchun.
    Bot instance inject qilinadi — dispatcher orqali.
    """

    async def check(self, update: Update) -> bool:
        # Admin ro'yxati update ga inject qilinadi dispatcher tomonidan
        is_admin = getattr(update, "_is_admin", False)
        return is_admin


class PremiumFilter(BaseFilter):
    """Faqat Telegram Premium foydalanuvchilar."""

    async def check(self, update: Update) -> bool:
        user = update.effective_user
        return user is not None and bool(user.is_premium)


# ─────────────────────────────────────────
# Matn filtrlari
# ─────────────────────────────────────────

class TextEqualsFilter(BaseFilter):
    """Aniq matn: @bot.on.message.text_equals("Ha", "Yo'q")"""

    def __init__(self, *texts: str, ignore_case: bool = False):
        self.ignore_case = ignore_case
        if ignore_case:
            self.texts = {t.lower() for t in texts}
        else:
            self.texts = set(texts)

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        if not msg or not msg.text:
            return False
        text = msg.text.lower() if self.ignore_case else msg.text
        return text in self.texts


class TextContainsFilter(BaseFilter):
    """Matn ichida kalit so'z: @bot.on.message.text_contains("salom")"""

    def __init__(self, *keywords: str, ignore_case: bool = True):
        self.ignore_case = ignore_case
        if ignore_case:
            self.keywords = [k.lower() for k in keywords]
        else:
            self.keywords = list(keywords)

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        if not msg or not msg.text:
            return False
        text = msg.text.lower() if self.ignore_case else msg.text
        return any(kw in text for kw in self.keywords)


# ─────────────────────────────────────────
# Album (Media Group) filtri
# ─────────────────────────────────────────

class AlbumFilter(BaseFilter):
    """
    @bot.on.message.album
    Bir nechta rasm/video birga kelganda ishlaydi.
    """

    async def check(self, update: Update) -> bool:
        msg = update.effective_message
        return msg is not None and msg.media_group_id is not None


# ─────────────────────────────────────────
# Dynamic filter — __getattr__ uchun
# ─────────────────────────────────────────

# ChainBuilder da ishlatiladigan dynamic filter nomlari → klasslari map
DYNAMIC_FILTERS: dict[str, BaseFilter] = {
    "message":       MessageFilter(),
    "edited":        EditedMessageFilter(),
    "callback":      CallbackFilter(),
    "inline":        InlineQueryFilter(),
    "private":       PrivateFilter,
    "group":         GroupFilter,
    "supergroup":    SupergroupFilter,
    "channel":       ChannelFilter,
    "text":          TextFilter,
    "photo":         PhotoFilter,
    "video":         VideoFilter,
    "audio":         AudioFilter,
    "document":      DocumentFilter,
    "voice":         VoiceFilter,
    "sticker":       StickerFilter,
    "location":      LocationFilter,
    "contact":       ContactFilter,
    "album":         AlbumFilter(),
    "admin_only":    AdminFilter(),
    "premium":       PremiumFilter(),
}