from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("telegrampy.contrib.i18n")


class I18n:
    """
    Ko'p tilli bot uchun internationalization tizimi.

    Papka strukturasi:
        locales/
            uz.json
            ru.json
            en.json

    Ishlatish:
        i18n = I18n(path="locales", default="uz")
        bot.provide(i18n=i18n)

        @bot.on.message.command("start")
        async def start(ctx, i18n):
            lang = ctx.user.language_code or "uz"
            await ctx.answer(i18n.get("welcome", lang))

    JSON fayl formati:
        {
            "welcome": "Xush kelibsiz!",
            "menu": "Menyu",
            "btn_help": "Yordam"
        }
    """

    def __init__(
        self,
        path: str | Path,
        default: str = "en",
        fallback: Optional[str] = None,
    ):
        self.default = default
        self.fallback = fallback or default
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load(Path(path))

    def _load(self, path: Path) -> None:
        if not path.exists():
            logger.warning(f"Locales papkasi topilmadi: {path}")
            return

        for file in path.glob("*.json"):
            lang = file.stem
            try:
                with open(file, encoding="utf-8") as f:
                    self._translations[lang] = json.load(f)
                logger.debug(f"Til yuklandi: {lang} ({len(self._translations[lang])} kalit)")
            except Exception as e:
                logger.error(f"Til yuklanmadi {file}: {e}")

        logger.info(f"I18n: {list(self._translations.keys())} tillari yuklandi")

    def get(
        self,
        key: str,
        lang: Optional[str] = None,
        **format_kwargs,
    ) -> str:
        """
        Tarjimani qaytaradi.

        i18n.get("welcome", "uz")
        i18n.get("greeting", "uz", name="Ali")  → "Salom, Ali!"
        """
        lang = lang or self.default

        # Asosiy til
        text = self._translations.get(lang, {}).get(key)

        # Fallback til
        if text is None and lang != self.fallback:
            text = self._translations.get(self.fallback, {}).get(key)

        # Kalit topilmasa — kalitni qaytaradi
        if text is None:
            logger.warning(f"Tarjima topilmadi: '{key}' ({lang})")
            return key

        # Format kwargs
        if format_kwargs:
            try:
                return text.format(**format_kwargs)
            except KeyError as e:
                logger.error(f"Format xatosi '{key}': {e}")
                return text

        return text

    def __call__(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """i18n("welcome", "uz") — qisqa chaqiriq."""
        return self.get(key, lang, **kwargs)

    @property
    def languages(self) -> list[str]:
        return list(self._translations.keys())

    def add_translation(self, lang: str, key: str, value: str) -> None:
        """Runtime da tarjima qo'shish."""
        if lang not in self._translations:
            self._translations[lang] = {}
        self._translations[lang][key] = value

    def reload(self, path: str | Path) -> None:
        """Tarjimalarni qayta yuklaydi."""
        self._translations.clear()
        self._load(Path(path))