from __future__ import annotations

import html
import re


# ─────────────────────────────────────────
# HTML escape
# ─────────────────────────────────────────

def escape(text: str) -> str:
    """HTML belgilarini xavfsiz qiladi: <, >, &, "."""
    return html.escape(str(text))


# ─────────────────────────────────────────
# HTML formatlash
# ─────────────────────────────────────────

def bold(text: str) -> str:
    return f"<b>{escape(text)}</b>"

def italic(text: str) -> str:
    return f"<i>{escape(text)}</i>"

def underline(text: str) -> str:
    return f"<u>{escape(text)}</u>"

def strike(text: str) -> str:
    return f"<s>{escape(text)}</s>"

def spoiler(text: str) -> str:
    return f"<tg-spoiler>{escape(text)}</tg-spoiler>"

def code(text: str) -> str:
    return f"<code>{escape(text)}</code>"

def pre(text: str, language: str = "") -> str:
    if language:
        return f'<pre><code class="language-{language}">{escape(text)}</code></pre>'
    return f"<pre>{escape(text)}</pre>"

def link(text: str, url: str) -> str:
    return f'<a href="{url}">{escape(text)}</a>'

def mention(text: str, user_id: int) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(text)}</a>'

def quote(text: str) -> str:
    return f"<blockquote>{escape(text)}</blockquote>"


# ─────────────────────────────────────────
# Markdown escape
# ─────────────────────────────────────────

_MD_SPECIAL = r"\_*[]()~`>#+-=|{}.!"

def escape_md(text: str) -> str:
    """MarkdownV2 uchun maxsus belgilarni escape qiladi."""
    return re.sub(r"([" + re.escape(_MD_SPECIAL) + r"])", r"\\\1", str(text))


# ─────────────────────────────────────────
# Markdown V2 formatlash
# ─────────────────────────────────────────

def md_bold(text: str) -> str:
    return f"*{escape_md(text)}*"

def md_italic(text: str) -> str:
    return f"_{escape_md(text)}_"

def md_code(text: str) -> str:
    return f"`{escape_md(text)}`"

def md_pre(text: str, language: str = "") -> str:
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"

def md_link(text: str, url: str) -> str:
    return f"[{escape_md(text)}]({url})"

def md_spoiler(text: str) -> str:
    return f"||{escape_md(text)}||"


# ─────────────────────────────────────────
# Yordamchi formatlash
# ─────────────────────────────────────────

def progress_bar(value: int, total: int, length: int = 10) -> str:
    """
    Oddiy progress bar:
    progress_bar(3, 10) → "███░░░░░░░ 30%"
    """
    if total == 0:
        return "░" * length + " 0%"
    filled = int(length * value / total)
    bar = "█" * filled + "░" * (length - filled)
    percent = int(100 * value / total)
    return f"{bar} {percent}%"


def number_format(n: int | float, sep: str = " ") -> str:
    """
    Sonni o'qimli formatga o'tkazadi:
    number_format(1000000) → "1 000 000"
    """
    return f"{n:,}".replace(",", sep)


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Uzun matnni qisqartiradi:
    truncate("Uzun matn", 8) → "Uzun ..."
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix