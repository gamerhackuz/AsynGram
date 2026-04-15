from __future__ import annotations

import re
from typing import Optional


_USERNAME_RE  = re.compile(r"^@?[a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9]$")
_PHONE_RE     = re.compile(r"^\+?[1-9]\d{6,14}$")
_URL_RE       = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
_BOT_TOKEN_RE = re.compile(r"^\d{8,10}:[a-zA-Z0-9_-]{35}$")


def is_valid_username(username: str) -> bool:
    """
    Telegram username to'g'riligini tekshiradi.
    "@username" yoki "username" formatida.
    """
    return bool(_USERNAME_RE.match(username.lstrip("@")))


def is_valid_phone(phone: str) -> bool:
    """
    Telefon raqam to'g'riligini tekshiradi.
    "+998901234567" yoki "998901234567" formatida.
    """
    clean = re.sub(r"[\s\-()]", "", phone)
    return bool(_PHONE_RE.match(clean))


def is_valid_url(url: str) -> bool:
    """URL to'g'riligini tekshiradi."""
    return bool(_URL_RE.match(url))


def is_valid_bot_token(token: str) -> bool:
    """Bot token formatini tekshiradi."""
    return bool(_BOT_TOKEN_RE.match(token))


def sanitize(text: str, max_length: Optional[int] = None) -> str:
    """
    Matnni tozalaydi:
    - Bosh va oxirdagi bo'shliqlarni olib tashlaydi
    - Ko'p bo'shliqlarni bittaga kamaytiradi
    - max_length ga qisqartiradi
    """
    cleaned = re.sub(r"\s+", " ", text.strip())
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def is_valid_callback_data(data: str) -> bool:
    """
    Callback data Telegram talablariga mosligini tekshiradi.
    Max 64 bayt bo'lishi kerak.
    """
    return len(data.encode("utf-8")) <= 64