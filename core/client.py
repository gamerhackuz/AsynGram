from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import aiohttp

from .types import Update
from ..utils.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramNotFoundError,
    TelegramBadRequestError,
)

logger = logging.getLogger("telegrampy.client")

BASE_URL = "https://api.telegram.org/bot{token}/{method}"
FILE_URL = "https://api.telegram.org/file/bot{token}/{path}"

# Retry sozlamalari
MAX_RETRIES = 5
RETRY_CODES = {500, 502, 503, 504}  # Server xatoliklari
RETRY_DELAYS = [0.5, 1, 2, 4, 8]   # Exponential backoff (sekund)


class TelegramClient:
    """
    Telegram Bot API bilan asenkron HTTP mijoz.

    Aiogramdan ustunligi:
    - Smart retry: 429 da Retry-After headerini o'qiydi, server xatoliklarida exponential backoff
    - Connection pooling: bitta session, minimal overhead
    - Batafsil logging: har bir so'rov/javob loglanadi
    - Timeout nazorati: connect + read alohida
    """

    def __init__(
        self,
        token: str,
        timeout: float = 30.0,
        connect_timeout: float = 10.0,
        max_retries: int = MAX_RETRIES,
    ):
        self.token = token
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries

        self._session: Optional[aiohttp.ClientSession] = None

    # ─────────────────────────────────────────
    # Session boshqaruvi
    # ─────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,           # Max parallel connections
                ttl_dns_cache=300,   # DNS cache 5 daqiqa
                enable_cleanup_closed=True,
            )
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=self.connect_timeout,
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "TelegramPy/1.0"},
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session yopildi")

    # ─────────────────────────────────────────
    # Asosiy so'rov
    # ─────────────────────────────────────────

    async def request(
        self,
        method: str,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> Any:
        """
        Telegram API ga so'rov yuboradi.
        Retry va error handling o'zi hal qiladi.
        """
        url = BASE_URL.format(token=self.token, method=method)
        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                result = await self._send(session, url, method, data, files)
                return result

            except TelegramRetryAfter as e:
                # 429: Telegram bizga kutishni buyurdi
                wait = e.retry_after + 0.5  # biroz qo'shimcha xavfsizlik
                logger.warning(
                    f"[{method}] Rate limit! {wait:.1f}s kutilmoqda... "
                    f"(urinish {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait)

            except TelegramAPIError as e:
                # Server xatoliklari (5xx) — retry qilish mumkin
                if e.status_code in RETRY_CODES and attempt < self.max_retries - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        f"[{method}] Server xatosi {e.status_code}. "
                        f"{delay}s dan keyin qayta urinish... "
                        f"(urinish {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

            except aiohttp.ClientConnectionError as e:
                if attempt < self.max_retries - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        f"[{method}] Ulanish xatosi: {e}. "
                        f"{delay}s dan keyin qayta urinish..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise TelegramNetworkError(f"Ulanib bo'lmadi: {e}") from e

            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        f"[{method}] Timeout. {delay}s dan keyin qayta urinish..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise TelegramNetworkError(f"[{method}] Timeout — server javob bermadi")

        raise TelegramNetworkError(f"[{method}] {self.max_retries} urinishdan keyin ham javob yo'q")

    async def _send(
        self,
        session: aiohttp.ClientSession,
        url: str,
        method: str,
        data: Optional[dict],
        files: Optional[dict],
    ) -> Any:
        """Bitta HTTP so'rovni yuboradi va javobni parse qiladi."""

        # File yuklash bo'lsa — multipart/form-data
        if files:
            form = aiohttp.FormData()
            if data:
                for key, value in data.items():
                    if value is not None:
                        form.add_field(key, str(value))
            for field_name, (filename, file_data, content_type) in files.items():
                form.add_field(field_name, file_data, filename=filename, content_type=content_type)
            response = await session.post(url, data=form)

        # Oddiy so'rov — JSON
        else:
            clean_data = {k: v for k, v in (data or {}).items() if v is not None}
            response = await session.post(url, json=clean_data if clean_data else None)

        return await self._parse_response(response, method)

    async def _parse_response(
        self,
        response: aiohttp.ClientResponse,
        method: str,
    ) -> Any:
        """HTTP javobni tahlil qiladi va xatolarni tasniflaydi."""

        status = response.status

        # Telegram ba'zan HTML qaytaradi (CloudFlare xatolari)
        content_type = response.content_type or ""
        if "application/json" not in content_type and status != 200:
            raise TelegramNetworkError(
                f"[{method}] Kutilmagan Content-Type: {content_type} (status={status})"
            )

        try:
            body = await response.json(content_type=None)
        except Exception as e:
            text = await response.text()
            raise TelegramNetworkError(
                f"[{method}] JSON parse xatosi: {e}\nJavob: {text[:200]}"
            ) from e

        # ✅ Muvaffaqiyatli
        if body.get("ok"):
            logger.debug(f"[{method}] OK ✓")
            return body["result"]

        # ❌ Telegram xatosi
        error_code = body.get("error_code", status)
        description = body.get("description", "Noma'lum xato")

        logger.error(f"[{method}] Xato {error_code}: {description}")

        # 429 — Rate limit
        if error_code == 429:
            params = body.get("parameters", {})
            retry_after = params.get("retry_after", 5)
            raise TelegramRetryAfter(retry_after=retry_after, description=description)

        # 403 — Bot bloklanган yoki ruxsat yo'q
        if error_code == 403:
            raise TelegramForbiddenError(description=description)

        # 404 — Chat/user topilmadi
        if error_code == 404:
            raise TelegramNotFoundError(description=description)

        # 400 — Noto'g'ri so'rov
        if error_code == 400:
            raise TelegramBadRequestError(description=description, method=method)

        # 5xx — Server xatoliklari (retry uchun)
        raise TelegramAPIError(
            status_code=error_code,
            description=description,
            method=method,
        )

    # ─────────────────────────────────────────
    # Fayl yuklab olish
    # ─────────────────────────────────────────

    async def download_file(self, file_path: str) -> bytes:
        """Telegram serveridan faylni yuklab oladi."""
        url = FILE_URL.format(token=self.token, path=file_path)
        session = await self._get_session()

        async with session.get(url) as response:
            if response.status != 200:
                raise TelegramNetworkError(
                    f"Fayl yuklab bo'lmadi: status={response.status}"
                )
            return await response.read()

    # ─────────────────────────────────────────
    # Context manager qo'llab-quvvatlash
    # ─────────────────────────────────────────

    async def __aenter__(self) -> "TelegramClient":
        await self._get_session()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()