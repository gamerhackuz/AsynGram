from __future__ import annotations

import logging
from typing import Callable, List, Optional, Pattern, Union

from .filters import (
    BaseFilter,
    DYNAMIC_FILTERS,
    CommandFilter,
    RegexFilter,
    StateFilter,
    CallbackDataFilter,
    CallbackDataStartFilter,
    CallbackDataRegexFilter,
    TextEqualsFilter,
    TextContainsFilter,
    UserIdFilter,
    LambdaFilter,
)
from .handler import HandlerRegistry

logger = logging.getLogger("telegrampy.router")


class ChainBuilder:
    """
    Fluent API orqali filterlar zanjirini quradi.

    Misol:
        @bot.on.message.private.command("start")
        @bot.on.callback.data_start("order_").state("waiting_confirm")
        @bot.on.message.private.text.regex(r"ID: (\\d+)").admin_only
    """

    def __init__(self, registry: HandlerRegistry, priority: int = 0):
        self._registry = registry
        self._filters: List[BaseFilter] = []
        self._priority = priority

    # ─────────────────────────────────────────
    # Dinamik filterlar — .private, .group, .text ...
    # ─────────────────────────────────────────

    def __getattr__(self, name: str) -> "ChainBuilder":
        if name.startswith("_"):
            raise AttributeError(name)

        if name in DYNAMIC_FILTERS:
            self._filters.append(DYNAMIC_FILTERS[name])
            return self

        # Noma'lum nom — custom dynamic filter sifatida qo'shiladi
        # Foydalanuvchi o'z custom filterini DYNAMIC_FILTERS ga qo'shishi mumkin
        logger.warning(
            f"Noma'lum filter: .{name!r} — DYNAMIC_FILTERS da topilmadi. "
            f"bot.register_filter('{name}', MyFilter()) bilan qo'shing."
        )
        
        return self

    # ─────────────────────────────────────────
    # Argumentli filterlar — IDE type hint uchun aniq metodlar
    # ─────────────────────────────────────────

    def command(self, *commands: str) -> "ChainBuilder":
        """
        @bot.on.message.command("start")
        @bot.on.message.command("start", "menu", "help")
        """
        self._filters.append(CommandFilter(*commands))
        return self

    def regex(self, pattern: Union[str, Pattern]) -> "ChainBuilder":
        """
        @bot.on.message.regex(r"ID: (\\d+)")
        ctx.match.group(1) orqali olinadi
        """
        self._filters.append(RegexFilter(pattern))
        return self

    def state(self, *states: str) -> "ChainBuilder":
        """
        @bot.on.message.state("waiting_name")
        @bot.on.message.state("*")  — istalgan active state
        """
        self._filters.append(StateFilter(*states))
        return self

    def data(self, *values: str) -> "ChainBuilder":
        """
        @bot.on.callback.data("confirm", "cancel")
        """
        self._filters.append(CallbackDataFilter(*values))
        return self

    def data_start(self, prefix: str) -> "ChainBuilder":
        """
        @bot.on.callback.data_start("order_")
        """
        self._filters.append(CallbackDataStartFilter(prefix))
        return self

    def data_regex(self, pattern: Union[str, Pattern]) -> "ChainBuilder":
        """
        @bot.on.callback.data_regex(r"item_(\\d+)")
        """
        self._filters.append(CallbackDataRegexFilter(pattern))
        return self

    def text_equals(self, *texts: str, ignore_case: bool = False) -> "ChainBuilder":
        """
        @bot.on.message.text_equals("Ha", "Yo'q")
        """
        self._filters.append(TextEqualsFilter(*texts, ignore_case=ignore_case))
        return self

    def text_contains(self, *keywords: str, ignore_case: bool = True) -> "ChainBuilder":
        """
        @bot.on.message.text_contains("salom", "hi")
        """
        self._filters.append(TextContainsFilter(*keywords, ignore_case=ignore_case))
        return self

    def user_id(self, *user_ids: int) -> "ChainBuilder":
        """
        @bot.on.message.user_id(123456789)
        """
        self._filters.append(UserIdFilter(*user_ids))
        return self

    def filter(self, *filters: BaseFilter) -> "ChainBuilder":
        """
        Istalgan custom filterni qo'shish:
        @bot.on.message.filter(MyCustomFilter())
        """
        self._filters.extend(filters)
        return self

    def when(self, func: Callable) -> "ChainBuilder":
        """
        Lambda bilan tezkor filter:
        @bot.on.message.when(lambda u: u.effective_user.is_premium)
        """
        self._filters.append(LambdaFilter(func))
        return self

    def priority(self, value: int) -> "ChainBuilder":
        """
        Handler priorityini belgilash:
        @bot.on.message.command("start").priority(10)
        """
        self._priority = value
        return self

    # ─────────────────────────────────────────
    # Yakunlovchi — dekorator sifatida ishlatiladi
    # ─────────────────────────────────────────

    def __call__(self, func: Callable) -> Callable:
        """
        @bot.on.message.command("start")
        async def handler(ctx): ...
        """
        self._registry.register(
            func=func,
            filters=list(self._filters),
            priority=self._priority,
        )
        logger.debug(
            f"Handler '{func.__name__}' ro'yxatga olindi | "
            f"Filterlar: {[type(f).__name__ for f in self._filters]}"
        )
        return func


# ─────────────────────────────────────────
# Router — bot.on ni boshqaradi
# ─────────────────────────────────────────

class Router:
    """
    Bot.on ga murojaat qilinganda yangi ChainBuilder qaytaradi.

    bot.on.message.command("start") → ChainBuilder
    """

    def __init__(self):
        self.registry = HandlerRegistry()
        self._custom_filters: dict[str, BaseFilter] = {}

    @property
    def on(self) -> ChainBuilder:
        """Har safar yangi ChainBuilder — filterlar aralashib ketmaydi."""
        return ChainBuilder(self.registry, priority=0)

    def register_filter(self, name: str, filter_instance: BaseFilter) -> None:
        """
        Custom filterni .name sifatida ishlatish uchun qo'shish:

            bot.register_filter("subscribed", SubscribedFilter())

            @bot.on.message.subscribed.command("start")
            async def handler(ctx): ...
        """
        DYNAMIC_FILTERS[name] = filter_instance
        self._custom_filters[name] = filter_instance
        logger.debug(f"Custom filter qo'shildi: .{name}")

    def include_router(self, router: "Router") -> None:
        """
        Boshqa routerning handlerlarini shu routerga qo'shish.
        Katta loyihalarda modullar bo'yicha ajratish uchun:

            admin_router = Router()
            bot.include_router(admin_router)
        """
        for handler in router.registry._handlers:
            self.registry._handlers.append(handler)
        self.registry._handlers.sort(key=lambda h: h.priority, reverse=True)
        logger.debug(
            f"Router qo'shildi: {len(router.registry)} ta handler import qilindi"
        )