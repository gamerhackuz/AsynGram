from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("telegrampy.injector")


class Injector:
    """
    Dependency Injection tizimi.

    bot.provide(db=db_session, config=my_config, redis=redis_client)

    @bot.on.message.command("balance")
    async def handler(ctx, db):       # db avtomatik inject qilinadi
        bal = await db.get_balance(ctx.user.id)
        await ctx.answer(f"Balans: {bal}")
    """

    def __init__(self):
        self._providers: Dict[str, Any] = {}

    def register(self, **kwargs: Any) -> None:
        """
        Dependency larni ro'yxatga olish.

        injector.register(db=db, redis=redis, config=config)
        """
        for name, value in kwargs.items():
            self._providers[name] = value
            logger.debug(f"Dependency ro'yxatga olindi: '{name}' → {type(value).__name__}")

    def unregister(self, *names: str) -> None:
        for name in names:
            self._providers.pop(name, None)

    async def inject(self, func: Callable, ctx: Any) -> Any:
        """
        Funksiya argumentlarini tekshirib, moslarini inject qiladi.

        Argumentlar:
        - 'ctx' — Context obyektini beradi
        - Boshqa nomlar — _providers dan qidiradi
        """
        sig = inspect.signature(func)
        kwargs: Dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            if param_name == "ctx":
                continue  # ctx birinchi argument — dispatcher beradi

            if param_name in self._providers:
                value = self._providers[param_name]
                # Provider callable bo'lsa (factory) — chaqiradi
                if callable(value) and not inspect.isclass(value):
                    try:
                        result = value()
                        if asyncio.iscoroutine(result):
                            result = await result
                        kwargs[param_name] = result
                    except Exception as e:
                        logger.error(f"Provider '{param_name}' xatosi: {e}")
                        if param.default is inspect.Parameter.empty:
                            raise
                else:
                    kwargs[param_name] = value

            elif param.default is inspect.Parameter.empty:
                # Majburiy argument topilmadi — ogohlantirish
                logger.warning(
                    f"'{func.__name__}' funksiyasida '{param_name}' argumenti "
                    f"topilmadi. bot.provide({param_name}=...) bilan qo'shing."
                )

        result = func(ctx, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def __contains__(self, name: str) -> bool:
        return name in self._providers

    def __repr__(self) -> str:
        return f"Injector(providers={list(self._providers.keys())})"