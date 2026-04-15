from __future__ import annotations

from typing import Optional


class TelegramPyError(Exception):
    """Barcha telegrampy xatoliklari uchun base."""
    pass


# ─────────────────────────────────────────
# Network xatoliklari
# ─────────────────────────────────────────

class TelegramNetworkError(TelegramPyError):
    """Internet muammosi, timeout, parse xatosi."""
    pass


# ─────────────────────────────────────────
# Telegram API xatoliklari
# ─────────────────────────────────────────

class TelegramAPIError(TelegramPyError):
    """Telegram API dan kelgan xato."""

    def __init__(self, status_code: int, description: str, method: str = ""):
        self.status_code = status_code
        self.description = description
        self.method = method
        super().__init__(f"[{method}] {status_code}: {description}")


class TelegramRetryAfter(TelegramAPIError):
    """429 — Rate limit. retry_after soniyadan keyin qayta urinish."""

    def __init__(self, retry_after: int, description: str = ""):
        self.retry_after = retry_after
        super().__init__(429, description, "")

    def __str__(self) -> str:
        return f"Rate limit! {self.retry_after}s kutish kerak."


class TelegramForbiddenError(TelegramAPIError):
    """403 — Bot bloklanган yoki guruhdan chiqarilgan."""

    def __init__(self, description: str = ""):
        super().__init__(403, description or "Forbidden")


class TelegramNotFoundError(TelegramAPIError):
    """404 — Chat yoki foydalanuvchi topilmadi."""

    def __init__(self, description: str = ""):
        super().__init__(404, description or "Not found")


class TelegramBadRequestError(TelegramAPIError):
    """400 — Noto'g'ri so'rov parametrlari."""

    def __init__(self, description: str = "", method: str = ""):
        super().__init__(400, description or "Bad request", method)


# ─────────────────────────────────────────
# Kutubxona ichki xatoliklari
# ─────────────────────────────────────────

class HandlerError(TelegramPyError):
    """Handler ichida yuz bergan xato."""
    pass


class FilterError(TelegramPyError):
    """Filter tekshirishda yuz bergan xato."""
    pass


class StateError(TelegramPyError):
    """FSM state boshqaruvida yuz bergan xato."""
    pass


class InjectorError(TelegramPyError):
    """Dependency injection da yuz bergan xato."""
    pass