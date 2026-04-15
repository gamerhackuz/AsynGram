from __future__ import annotations

import json
from typing import List, Optional

from .builder import KeyboardBuilder


class ReplyKeyboardBuilder(KeyboardBuilder):
    """
    Reply keyboard builder — fluent API.

    kb = ReplyKeyboardBuilder()
    kb.text("📋 Menyu").text("⚙️ Sozlamalar").row()
    kb.text("📞 Telefon", request_contact=True).row()
    kb.adjust(2)

    await ctx.answer("Tanlang:", reply_markup=kb)
    """

    def __init__(
        self,
        resize: bool = True,
        one_time: bool = False,
        placeholder: Optional[str] = None,
    ):
        super().__init__()
        self._resize = resize
        self._one_time = one_time
        self._placeholder = placeholder

    # ─────────────────────────────────────────
    # Tugma turlari
    # ─────────────────────────────────────────

    def text(self, text: str) -> "ReplyKeyboardBuilder":
        """Oddiy matn tugma."""
        self._current_row.append({"text": text})
        return self

    def contact(self, text: str = "📞 Telefon raqamni yuborish") -> "ReplyKeyboardBuilder":
        """Kontakt so'rash tugmasi."""
        self._current_row.append({"text": text, "request_contact": True})
        return self

    def location(self, text: str = "📍 Joylashuvni yuborish") -> "ReplyKeyboardBuilder":
        """Joylashuv so'rash tugmasi."""
        self._current_row.append({"text": text, "request_location": True})
        return self

    def poll(self, text: str, poll_type: Optional[str] = None) -> "ReplyKeyboardBuilder":
        """So'rovnoma tugmasi."""
        btn = {"text": text, "request_poll": {}}
        if poll_type:
            btn["request_poll"]["type"] = poll_type
        self._current_row.append(btn)
        return self

    def web_app(self, text: str, url: str) -> "ReplyKeyboardBuilder":
        """Web App tugma."""
        self._current_row.append({"text": text, "web_app": {"url": url}})
        return self

    # ─────────────────────────────────────────
    # Sozlamalar
    # ─────────────────────────────────────────

    def one_time(self) -> "ReplyKeyboardBuilder":
        """Bir marta bosilgandan keyin keyboardni yashiradi."""
        self._one_time = True
        return self

    def no_resize(self) -> "ReplyKeyboardBuilder":
        """Keyboardni resize qilmaydi."""
        self._resize = False
        return self

    def set_placeholder(self, text: str) -> "ReplyKeyboardBuilder":
        """Input field placeholder matni."""
        self._placeholder = text
        return self

    # ─────────────────────────────────────────
    # Markup yaratish
    # ─────────────────────────────────────────

    def as_markup(self) -> dict:
        markup = {
            "keyboard": self._flush(),
            "resize_keyboard": self._resize,
        }
        if self._one_time:
            markup["one_time_keyboard"] = True
        if self._placeholder:
            markup["input_field_placeholder"] = self._placeholder
        return markup

    def as_json(self) -> str:
        return json.dumps(self.as_markup(), ensure_ascii=False)

    def __repr__(self) -> str:
        rows = self._flush()
        total = sum(len(r) for r in rows)
        return f"ReplyKeyboardBuilder({total} buttons, {len(rows)} rows)"


class ReplyKeyboardRemove:
    """Reply keyboardni olib tashlaydi."""

    def as_markup(self) -> dict:
        return {"remove_keyboard": True}

    def as_json(self) -> str:
        return json.dumps(self.as_markup())