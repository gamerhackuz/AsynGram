from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any, Callable, Iterable, List, Optional, TypeVar

T = TypeVar("T")


def parse_command(text: str) -> tuple[str, str]:
    """
    Komanda va argumentlarni ajratadi.
    "/start hello world" → ("start", "hello world")
    """
    if not text or not text.startswith("/"):
        return "", text
    parts = text.split(maxsplit=1)
    command = parts[0].lstrip("/").split("@")[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return command, args


def extract_args(text: str) -> List[str]:
    """
    Komanda argumentlarini ro'yxat sifatida qaytaradi.
    "/ban 123 spam" → ["123", "spam"]
    """
    _, args = parse_command(text)
    return args.split() if args else []


def get_chat_type(chat_type: str) -> str:
    """Chat turini o'qimli formatga o'tkazadi."""
    mapping = {
        "private": "Shaxsiy",
        "group": "Guruh",
        "supergroup": "Superguruh",
        "channel": "Kanal",
    }
    return mapping.get(chat_type, chat_type)


def chunks(lst: List[T], n: int) -> Iterable[List[T]]:
    """
    Ro'yxatni n o'lchamli bo'laklarga bo'ladi.
    chunks([1,2,3,4,5], 2) → [[1,2], [3,4], [5]]
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_id(prefix: str = "") -> str:
    """
    Qisqa unikal ID yaratadi.
    generate_id("order") → "order_a3f9b2"
    """
    raw = f"{prefix}{time.time()}".encode()
    short = hashlib.md5(raw).hexdigest()[:6]
    return f"{prefix}_{short}" if prefix else short


async def run_sync(func: Callable, *args, **kwargs) -> Any:
    """
    Sinxron funksiyani async kontekstda bloklashsiz ishlatish.
    Masalan: DB so'rovlari uchun.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def safe_int(value: Any, default: int = 0) -> int:
    """Xatoliksiz int ga o'tkazish."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def mention_html(full_name: str, user_id: int) -> str:
    """HTML mention yaratadi."""
    from .formatting import escape
    return f'<a href="tg://user?id={user_id}">{escape(full_name)}</a>'