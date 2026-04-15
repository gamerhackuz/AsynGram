from __future__ import annotations

from typing import List, Optional


class KeyboardBuilder:
    """
    Barcha keyboard builderlar uchun base klass.
    InlineKeyboardBuilder va ReplyKeyboardBuilder shu klassdan meros oladi.
    """

    def __init__(self):
        self._rows: List[List[dict]] = []
        self._current_row: List[dict] = []

    def _make_button(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    def add(self, *buttons: dict) -> "KeyboardBuilder":
        """Tugmalarni joriy qatorga qo'shadi."""
        for btn in buttons:
            self._current_row.append(btn)
        return self

    def row(self, *buttons: dict) -> "KeyboardBuilder":
        """
        Joriy qatorni saqlaydi va yangi qator boshlaydi.

        .row(btn1, btn2)  →  [[btn1, btn2]]
        """
        if self._current_row:
            self._rows.append(self._current_row)
            self._current_row = []
        if buttons:
            self._rows.append(list(buttons))
        return self

    def adjust(self, *widths: int) -> "KeyboardBuilder":
        """
        Barcha tugmalarni berilgan kengliklar bo'yicha qatorlarga bo'ladi.

        .adjust(2, 2, 1)  →  [2 ta, 2 ta, 1 ta]
        .adjust(2)        →  har qatorda 2 ta
        """
        # Barcha tugmalarni tekis ro'yxatga olamiz
        all_buttons = []
        for row in self._rows:
            all_buttons.extend(row)
        if self._current_row:
            all_buttons.extend(self._current_row)

        self._rows = []
        self._current_row = []

        index = 0
        width_index = 0

        while index < len(all_buttons):
            width = widths[min(width_index, len(widths) - 1)]
            self._rows.append(all_buttons[index:index + width])
            index += width
            width_index += 1

        return self

    def _flush(self) -> List[List[dict]]:
        """Joriy qatorni saqlaydi va barcha qatorlarni qaytaradi."""
        rows = list(self._rows)
        if self._current_row:
            rows.append(self._current_row)
        return rows

    def as_markup(self) -> dict:
        raise NotImplementedError