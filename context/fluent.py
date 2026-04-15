from __future__ import annotations

import json
from typing import Any, List, Optional, Union


class MessageBuilder:
    """
    Lazy execution pattern — await yozilganda xabar yuboriladi.

    await ctx.answer("Salom!")
    await ctx.answer("Menyu:").inline_row(btn1, btn2)
    await ctx.answer("Ro'yxat:").inline_auto([btn1, btn2, btn3], width=2)
    await ctx.answer("Matn").keyboard(["Ha", "Yo'q"])
    """

    def __init__(
        self,
        bot: Any,
        chat_id: int,
        text: str,
        mode: str = "send",           # send | edit
        message_id: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[str] = None,
        **kwargs,
    ):
        self._bot = bot
        self._chat_id = chat_id
        self._text = text
        self._mode = mode
        self._message_id = message_id
        self._reply_to_message_id = reply_to_message_id
        self._parse_mode = parse_mode
        self._disable_web_page_preview = disable_web_page_preview
        self._external_markup = reply_markup

        # Keyboard
        self._inline_keyboard: List[List[dict]] = []
        self._reply_keyboard: List[List[str]] = []
        self._remove_keyboard: bool = False
        self._keyboard_mode: Optional[str] = None  # inline | reply | remove

    # ─────────────────────────────────────────
    # Inline keyboard
    # ─────────────────────────────────────────

    def inline_row(self, *buttons: dict) -> "MessageBuilder":
        """
        Bir qator inline tugmalar qo'shadi.

        .inline_row(ctx.btn.callback("A", "a"), ctx.btn.callback("B", "b"))
        """
        self._inline_keyboard.append(list(buttons))
        self._keyboard_mode = "inline"
        return self

    def inline_auto(self, buttons: List[dict], width: int = 2) -> "MessageBuilder":
        """
        Tugmalarni avtomatik qatorlarga bo'ladi.

        .inline_auto([btn1, btn2, btn3, btn4], width=2)
        → [[btn1, btn2], [btn3, btn4]]
        """
        for i in range(0, len(buttons), width):
            self._inline_keyboard.append(buttons[i:i + width])
        self._keyboard_mode = "inline"
        return self

    def inline_column(self, *buttons: dict) -> "MessageBuilder":
        """
        Har bir tugmani alohida qatorga qo'yadi.

        .inline_column(btn1, btn2, btn3)
        → [[btn1], [btn2], [btn3]]
        """
        for btn in buttons:
            self._inline_keyboard.append([btn])
        self._keyboard_mode = "inline"
        return self

    # ─────────────────────────────────────────
    # Reply keyboard
    # ─────────────────────────────────────────

    def keyboard(self, buttons: List[Union[str, List[str]]], **kwargs) -> "MessageBuilder":
        """
        Reply keyboard qo'shadi.

        .keyboard(["Ha", "Yo'q"])
        .keyboard([["Ha", "Yo'q"], ["Bekor qilish"]])
        """
        self._reply_keyboard_kwargs = kwargs
        for row in buttons:
            if isinstance(row, str):
                self._reply_keyboard.append([row])
            else:
                self._reply_keyboard.append(row)
        self._keyboard_mode = "reply"
        return self

    def remove_keyboard(self) -> "MessageBuilder":
        """Reply keyboardni olib tashlaydi."""
        self._remove_keyboard = True
        self._keyboard_mode = "remove"
        return self

    # ─────────────────────────────────────────
    # Matn sozlamalari
    # ─────────────────────────────────────────

    def no_preview(self) -> "MessageBuilder":
        """Web page preview o'chiriladi."""
        self._disable_web_page_preview = True
        return self

    def markdown(self) -> "MessageBuilder":
        """Parse mode Markdown ga o'zgartiriladi."""
        self._parse_mode = "Markdown"
        return self

    def no_parse(self) -> "MessageBuilder":
        """Parse mode o'chiriladi."""
        self._parse_mode = None
        return self

    # ─────────────────────────────────────────
    # Keyboard build
    # ─────────────────────────────────────────

    def _build_markup(self) -> Optional[str]:
        if self._external_markup:      # ← QO'SHING
            return self._external_markup
        if self._keyboard_mode == "inline" and self._inline_keyboard:
            return json.dumps({
                "inline_keyboard": self._inline_keyboard
            })
        
    
        
        
        if self._keyboard_mode == "reply" and self._reply_keyboard:
            rows = []
            for row in self._reply_keyboard:
                rows.append([{"text": btn} for btn in row])
            markup = {
                "keyboard": rows,
                "resize_keyboard": True,
            }
            if hasattr(self, "_reply_keyboard_kwargs"):
                markup.update(self._reply_keyboard_kwargs)
            return json.dumps(markup)

        if self._keyboard_mode == "remove":
            return json.dumps({"remove_keyboard": True})

        return None

    # ─────────────────────────────────────────
    # Lazy execution — await shu yerda ishlaydi
    # ─────────────────────────────────────────

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        markup = self._build_markup()
        print("MARKUP:", markup)

        if self._mode == "edit":
            return await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=self._text,
                parse_mode=self._parse_mode,
                reply_markup=markup,
                disable_web_page_preview=self._disable_web_page_preview,
            )

        return await self._bot.send_message(
            chat_id=self._chat_id,
            text=self._text,
            parse_mode=self._parse_mode,
            reply_markup=markup,
            reply_to_message_id=self._reply_to_message_id,
            disable_web_page_preview=self._disable_web_page_preview,
        )