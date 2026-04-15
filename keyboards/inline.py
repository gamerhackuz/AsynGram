from __future__ import annotations

import json
from typing import List, Optional

from .builder import KeyboardBuilder


class InlineKeyboardBuilder(KeyboardBuilder):
    """
    Inline keyboard builder — fluent API.

    kb = InlineKeyboardBuilder()
    kb.callback("✅ Ha", "confirm").callback("❌ Yo'q", "cancel").row()
    kb.url("Sayt", "https://example.com")
    kb.adjust(2)

    await ctx.answer("Tanlang:", reply_markup=kb)
    """

    # ─────────────────────────────────────────
    # Tugma turlari
    # ─────────────────────────────────────────

    def callback(self, text: str, data: str) -> "InlineKeyboardBuilder":
        """Callback tugma qo'shadi."""
        self._current_row.append({"text": text, "callback_data": data})
        return self

    def url(self, text: str, url: str) -> "InlineKeyboardBuilder":
        """URL tugma qo'shadi."""
        self._current_row.append({"text": text, "url": url})
        return self

    def web_app(self, text: str, url: str) -> "InlineKeyboardBuilder":
        """Web App tugma qo'shadi."""
        self._current_row.append({"text": text, "web_app": {"url": url}})
        return self

    def switch_inline(self, text: str, query: str = "") -> "InlineKeyboardBuilder":
        """Inline query tugma qo'shadi."""
        self._current_row.append({"text": text, "switch_inline_query": query})
        return self

    def switch_inline_current(self, text: str, query: str = "") -> "InlineKeyboardBuilder":
        """Joriy chatda inline query tugma."""
        self._current_row.append({"text": text, "switch_inline_query_current_chat": query})
        return self

    def pay(self, text: str) -> "InlineKeyboardBuilder":
        """To'lov tugmasi (invoice uchun)."""
        self._current_row.append({"text": text, "pay": True})
        return self

    # ─────────────────────────────────────────
    # Row shortcutlari
    # ─────────────────────────────────────────

    def row(self, *buttons) -> "InlineKeyboardBuilder":
        """Qatorni yakunlaydi."""
        if self._current_row:
            self._rows.append(self._current_row)
            self._current_row = []
        if buttons:
            row = []
            for btn in buttons:
                if isinstance(btn, dict):
                    row.append(btn)
            if row:
                self._rows.append(row)
        return self

    # ─────────────────────────────────────────
    # Markup yaratish
    # ─────────────────────────────────────────

    def as_markup(self) -> dict:
        return {"inline_keyboard": self._flush()}

    def as_json(self) -> str:
        return json.dumps(self.as_markup(), ensure_ascii=False)

    def __repr__(self) -> str:
        rows = self._flush()
        total = sum(len(r) for r in rows)
        return f"InlineKeyboardBuilder({total} buttons, {len(rows)} rows)"