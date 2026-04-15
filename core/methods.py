from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, Union

from .types import (
    Message,
    Update,
    User,
    Chat,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# Universal fayl tipi — foydalanuvchi xohlagan narsani berishi mumkin
FileInput = Union[str, bytes, BinaryIO, Path]

# Keyboard tipi
KeyboardInput = Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, dict, None]


# ─────────────────────────────────────────
# Ichki yordamchi funksiyalar
# ─────────────────────────────────────────

def _resolve_file(value: FileInput) -> tuple[Optional[str], Optional[tuple]]:
    """
    FileInput ni tahlil qiladi.
    Qaytaradi: (json_value, file_tuple)
    - json_value: file_id yoki URL bo'lsa — string
    - file_tuple: (filename, data, content_type) — upload kerak bo'lsa
    """
    # String: file_id yoki URL
    if isinstance(value, str):
        return value, None

    # Path obyekti: local fayl
    if isinstance(value, Path):
        data = value.read_bytes()
        return None, (value.name, data, "application/octet-stream")

    # Bytes
    if isinstance(value, bytes):
        return None, ("file", value, "application/octet-stream")

    # File-like object (open(), BytesIO, ...)
    if hasattr(value, "read"):
        filename = getattr(value, "name", "file")
        filename = Path(filename).name if filename else "file"
        data = value.read()
        return None, (filename, data, "application/octet-stream")

    raise TypeError(f"Noto'g'ri fayl turi: {type(value)}")


def _serialize_keyboard(keyboard: KeyboardInput) -> Optional[str]:
    if keyboard is None:
        return None
    if isinstance(keyboard, str):
        return keyboard
    if isinstance(keyboard, dict):
        return json.dumps(keyboard)
    return keyboard.model_dump_json(exclude_none=True)


def _clean(data: dict) -> dict:
    """None qiymatlarni olib tashlaydi."""
    return {k: v for k, v in data.items() if v is not None}


# ─────────────────────────────────────────
# Methods mixin — Bot va Client bu klassdan meros oladi
# ─────────────────────────────────────────

class TelegramMethods:
    """
    Barcha Telegram API metodlari shu klassda.
    self._client.request(method, data, files) orqali ishlaydi.
    """

    async def _call(
        self,
        method: str,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> Any:
        raise NotImplementedError  # Bot klassi override qiladi

    # ─────────────────────────────────────────
    # getMe / getUpdates / setWebhook
    # ─────────────────────────────────────────

    async def get_me(self) -> User:
        result = await self._call("getMe")
        return User(**result)

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Optional[List[str]] = None,
    ) -> List[Update]:
        data = _clean({
            "offset": offset,
            "limit": limit,
            "timeout": timeout,
            "allowed_updates": json.dumps(allowed_updates) if allowed_updates else None,
        })
        results = await self._call("getUpdates", data)
        print("RAW:", results)
        
        return [Update(**u) for u in results]

    async def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None,
        allowed_updates: Optional[List[str]] = None,
        max_connections: int = 40,
    ) -> bool:
        data = _clean({
            "url": url,
            "secret_token": secret_token,
            "max_connections": max_connections,
            "allowed_updates": json.dumps(allowed_updates) if allowed_updates else json.dumps(["message", "callback_query", "inline_query"]),
        })
        return await self._call("setWebhook", data)

    async def delete_webhook(self, drop_pending_updates: bool = False) -> bool:
        return await self._call("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    # ─────────────────────────────────────────
    # Xabar yuborish
    # ─────────────────────────────────────────

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: KeyboardInput = None,
        reply_to_message_id: Optional[int] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": _serialize_keyboard(reply_markup),
            "reply_to_message_id": reply_to_message_id,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
            "protect_content": protect_content,
        })
        print("SENDING DATA:", data)
        result = await self._call("sendMessage", data)
        return Message(**result)

    async def edit_message_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: KeyboardInput = None,
        disable_web_page_preview: Optional[bool] = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": _serialize_keyboard(reply_markup),
            "disable_web_page_preview": disable_web_page_preview,
        })
        result = await self._call("editMessageText", data)
        return Message(**result)

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        return await self._call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        })
        result = await self._call("forwardMessage", data)
        return Message(**result)

    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: Optional[str] = None,
        reply_markup: KeyboardInput = None,
    ) -> dict:
        data = _clean({
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "caption": caption,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        return await self._call("copyMessage", data)

    async def pin_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: bool = False,
    ) -> bool:
        return await self._call("pinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        })

    async def unpin_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        return await self._call("unpinChatMessage", {"chat_id": chat_id, "message_id": message_id})

    # ─────────────────────────────────────────
    # Media yuborish — Universal FileInput
    # ─────────────────────────────────────────

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: FileInput,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        reply_markup: KeyboardInput = None,
        reply_to_message_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(photo)
        data = _clean({
            "chat_id": chat_id,
            "photo": json_val,
            "caption": caption,
            "parse_mode": parse_mode,
            "reply_markup": _serialize_keyboard(reply_markup),
            "reply_to_message_id": reply_to_message_id,
            "disable_notification": disable_notification,
        })
        files = {"photo": file_tuple} if file_tuple else None
        result = await self._call("sendPhoto", data, files)
        return Message(**result)

    async def send_video(
        self,
        chat_id: Union[int, str],
        video: FileInput,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[FileInput] = None,
        reply_markup: KeyboardInput = None,
        reply_to_message_id: Optional[int] = None,
        supports_streaming: Optional[bool] = True,
    ) -> Message:
        json_val, file_tuple = _resolve_file(video)
        thumb_json, thumb_file = _resolve_file(thumbnail) if thumbnail else (None, None)

        data = _clean({
            "chat_id": chat_id,
            "video": json_val,
            "caption": caption,
            "parse_mode": parse_mode,
            "duration": duration,
            "width": width,
            "height": height,
            "thumbnail": thumb_json,
            "supports_streaming": supports_streaming,
            "reply_markup": _serialize_keyboard(reply_markup),
            "reply_to_message_id": reply_to_message_id,
        })
        files = {}
        if file_tuple:   files["video"] = file_tuple
        if thumb_file:   files["thumbnail"] = thumb_file
        result = await self._call("sendVideo", data, files or None)
        return Message(**result)

    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: FileInput,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(audio)
        data = _clean({
            "chat_id": chat_id,
            "audio": json_val,
            "caption": caption,
            "parse_mode": parse_mode,
            "duration": duration,
            "performer": performer,
            "title": title,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        files = {"audio": file_tuple} if file_tuple else None
        result = await self._call("sendAudio", data, files)
        return Message(**result)

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: FileInput,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        thumbnail: Optional[FileInput] = None,
        reply_markup: KeyboardInput = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(document)
        thumb_json, thumb_file = _resolve_file(thumbnail) if thumbnail else (None, None)

        data = _clean({
            "chat_id": chat_id,
            "document": json_val,
            "caption": caption,
            "parse_mode": parse_mode,
            "thumbnail": thumb_json,
            "reply_markup": _serialize_keyboard(reply_markup),
            "reply_to_message_id": reply_to_message_id,
        })
        files = {}
        if file_tuple: files["document"] = file_tuple
        if thumb_file: files["thumbnail"] = thumb_file
        result = await self._call("sendDocument", data, files or None)
        return Message(**result)

    async def send_voice(
        self,
        chat_id: Union[int, str],
        voice: FileInput,
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(voice)
        data = _clean({
            "chat_id": chat_id,
            "voice": json_val,
            "caption": caption,
            "duration": duration,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        files = {"voice": file_tuple} if file_tuple else None
        result = await self._call("sendVoice", data, files)
        return Message(**result)

    async def send_video_note(
        self,
        chat_id: Union[int, str],
        video_note: FileInput,
        duration: Optional[int] = None,
        length: Optional[int] = None,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(video_note)
        data = _clean({
            "chat_id": chat_id,
            "video_note": json_val,
            "duration": duration,
            "length": length,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        files = {"video_note": file_tuple} if file_tuple else None
        result = await self._call("sendVideoNote", data, files)
        return Message(**result)

    async def send_sticker(
        self,
        chat_id: Union[int, str],
        sticker: FileInput,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        json_val, file_tuple = _resolve_file(sticker)
        data = _clean({
            "chat_id": chat_id,
            "sticker": json_val,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        files = {"sticker": file_tuple} if file_tuple else None
        result = await self._call("sendSticker", data, files)
        return Message(**result)

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        reply_markup: KeyboardInput = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "reply_markup": _serialize_keyboard(reply_markup),
            "reply_to_message_id": reply_to_message_id,
        })
        result = await self._call("sendLocation", data)
        return Message(**result)

    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        result = await self._call("sendContact", data)
        return Message(**result)

    async def send_chat_action(
        self,
        chat_id: Union[int, str],
        action: str,  # typing | upload_photo | upload_video | record_voice ...
    ) -> bool:
        return await self._call("sendChatAction", {"chat_id": chat_id, "action": action})

    # ─────────────────────────────────────────
    # Media Group (Album) — Killer Feature
    # ─────────────────────────────────────────

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[Union[FileInput, dict]],
        media_type: str = "photo",  # photo | video | document | audio
        captions: Optional[List[str]] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> List[Message]:
        """
        Album yuboradi. Foydalanuvchi shunchaki fayllar ro'yxatini beradi —
        library InputMedia obyektlariga o'zi aylantiradi.

        Misol:
            await bot.send_media_group(chat_id, [photo1, photo2, photo3])
        """
        media_list = []
        files = {}

        for i, item in enumerate(media):
            caption = (captions[i] if captions and i < len(captions) else None)

            # Agar foydalanuvchi dict bersa — to'g'ridan-to'g'ri ishlatamiz
            if isinstance(item, dict):
                media_list.append(item)
                continue

            json_val, file_tuple = _resolve_file(item)

            if file_tuple:
                attach_name = f"file_{i}"
                files[attach_name] = file_tuple
                media_entry = {
                    "type": media_type,
                    "media": f"attach://{attach_name}",
                }
            else:
                media_entry = {
                    "type": media_type,
                    "media": json_val,
                }

            if caption:
                media_entry["caption"] = caption
                media_entry["parse_mode"] = "HTML"

            media_list.append(media_entry)

        data = _clean({
            "chat_id": chat_id,
            "media": json.dumps(media_list),
            "reply_to_message_id": reply_to_message_id,
        })
        results = await self._call("sendMediaGroup", data, files or None)
        return [Message(**r) for r in results]

    # ─────────────────────────────────────────
    # Callback Query
    # ─────────────────────────────────────────

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0,
    ) -> bool:
        data = _clean({
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
            "url": url,
            "cache_time": cache_time,
        })
        return await self._call("answerCallbackQuery", data)

    async def edit_message_reply_markup(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: KeyboardInput = None,
    ) -> Message:
        data = _clean({
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": _serialize_keyboard(reply_markup),
        })
        result = await self._call("editMessageReplyMarkup", data)
        return Message(**result)

    # ─────────────────────────────────────────
    # Chat boshqaruvi
    # ─────────────────────────────────────────

    async def get_chat(self, chat_id: Union[int, str]) -> Chat:
        result = await self._call("getChat", {"chat_id": chat_id})
        return Chat(**result)

    async def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        return await self._call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def get_chat_member_count(self, chat_id: Union[int, str]) -> int:
        return await self._call("getChatMemberCount", {"chat_id": chat_id})

    async def ban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[int] = None,
    ) -> bool:
        data = _clean({"chat_id": chat_id, "user_id": user_id, "until_date": until_date})
        return await self._call("banChatMember", data)

    async def unban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        only_if_banned: bool = True,
    ) -> bool:
        return await self._call("unbanChatMember", {
            "chat_id": chat_id,
            "user_id": user_id,
            "only_if_banned": only_if_banned,
        })

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        permissions: dict,
        until_date: Optional[int] = None,
    ) -> bool:
        data = _clean({
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": json.dumps(permissions),
            "until_date": until_date,
        })
        return await self._call("restrictChatMember", data)

    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        can_manage_chat: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
    ) -> bool:
        data = _clean({
            "chat_id": chat_id,
            "user_id": user_id,
            "can_manage_chat": can_manage_chat,
            "can_delete_messages": can_delete_messages,
            "can_post_messages": can_post_messages,
            "can_edit_messages": can_edit_messages,
            "can_pin_messages": can_pin_messages,
        })
        return await self._call("promoteChatMember", data)

    async def leave_chat(self, chat_id: Union[int, str]) -> bool:
        return await self._call("leaveChat", {"chat_id": chat_id})

    # ─────────────────────────────────────────
    # Fayl
    # ─────────────────────────────────────────

    async def get_file(self, file_id: str) -> dict:
        return await self._call("getFile", {"file_id": file_id})

    # ─────────────────────────────────────────
    # Bot commands
    # ─────────────────────────────────────────

    async def set_my_commands(
        self,
        commands: List[dict],
        scope: Optional[dict] = None,
        language_code: Optional[str] = None,
    ) -> bool:
        data = _clean({
            "commands": json.dumps(commands),
            "scope": json.dumps(scope) if scope else None,
            "language_code": language_code,
        })
        return await self._call("setMyCommands", data)

    async def delete_my_commands(self) -> bool:
        return await self._call("deleteMyCommands")