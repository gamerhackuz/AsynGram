from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────
# Base
# ─────────────────────────────────────────

class TelegramObject(BaseModel):
    class Config:
        extra = "allow"


# ─────────────────────────────────────────
# User & Chat
# ─────────────────────────────────────────

class User(TelegramObject):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.id}">{self.full_name}</a>'


class ChatPhoto(TelegramObject):
    small_file_id: str
    big_file_id: str


class Chat(TelegramObject):
    id: int
    type: str  # private | group | supergroup | channel
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    photo: Optional[ChatPhoto] = None
    description: Optional[str] = None
    invite_link: Optional[str] = None
    is_forum: Optional[bool] = None

    @property
    def is_private(self) -> bool:
        return self.type == "private"

    @property
    def is_group(self) -> bool:
        return self.type in ("group", "supergroup")

    @property
    def is_channel(self) -> bool:
        return self.type == "channel"


# ─────────────────────────────────────────
# Media Types
# ─────────────────────────────────────────

class PhotoSize(TelegramObject):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class Video(TelegramObject):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    thumbnail: Optional[PhotoSize] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class Audio(TelegramObject):
    file_id: str
    file_unique_id: str
    duration: int
    performer: Optional[str] = None
    title: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    thumbnail: Optional[PhotoSize] = None


class Document(TelegramObject):
    file_id: str
    file_unique_id: str
    thumbnail: Optional[PhotoSize] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class Voice(TelegramObject):
    file_id: str
    file_unique_id: str
    duration: int
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class VideoNote(TelegramObject):
    file_id: str
    file_unique_id: str
    length: int
    duration: int
    thumbnail: Optional[PhotoSize] = None
    file_size: Optional[int] = None


class Sticker(TelegramObject):
    file_id: str
    file_unique_id: str
    type: str
    width: int
    height: int
    is_animated: bool
    is_video: bool
    thumbnail: Optional[PhotoSize] = None
    emoji: Optional[str] = None
    file_size: Optional[int] = None


class Location(TelegramObject):
    longitude: float
    latitude: float
    horizontal_accuracy: Optional[float] = None


class Contact(TelegramObject):
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    user_id: Optional[int] = None


# ─────────────────────────────────────────
# Keyboard Types
# ─────────────────────────────────────────

class InlineKeyboardButton(TelegramObject):
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    web_app: Optional[dict] = None
    switch_inline_query: Optional[str] = None
    switch_inline_query_current_chat: Optional[str] = None


class InlineKeyboardMarkup(TelegramObject):
    inline_keyboard: List[List[InlineKeyboardButton]] = Field(default_factory=list)


class KeyboardButton(TelegramObject):
    text: str
    request_contact: Optional[bool] = None
    request_location: Optional[bool] = None


class ReplyKeyboardMarkup(TelegramObject):
    keyboard: List[List[KeyboardButton]] = Field(default_factory=list)
    resize_keyboard: Optional[bool] = True
    one_time_keyboard: Optional[bool] = None
    input_field_placeholder: Optional[str] = None


class ReplyKeyboardRemove(TelegramObject):
    remove_keyboard: bool = True


# ─────────────────────────────────────────
# Message Entity
# ─────────────────────────────────────────

class MessageEntity(TelegramObject):
    type: str  # mention | hashtag | bot_command | url | bold | italic | code ...
    offset: int
    length: int
    url: Optional[str] = None
    user: Optional[User] = None
    language: Optional[str] = None


# ─────────────────────────────────────────
# Message
# ─────────────────────────────────────────

class Message(TelegramObject):
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = Field(None, alias="from")
    text: Optional[str] = None
    caption: Optional[str] = None
    entities: Optional[List[MessageEntity]] = None

    # Media fields (alohida + universal .media property)
    photo: Optional[List[PhotoSize]] = None
    video: Optional[Video] = None
    audio: Optional[Audio] = None
    document: Optional[Document] = None
    voice: Optional[Voice] = None
    video_note: Optional[VideoNote] = None
    sticker: Optional[Sticker] = None
    animation: Optional[Video] = None

    # Other content
    location: Optional[Location] = None
    contact: Optional[Contact] = None

    # Forwarded
    forward_from: Optional[User] = None
    forward_from_chat: Optional[Chat] = None
    forward_date: Optional[int] = None

    # Reply
    reply_to_message: Optional["Message"] = None

    # Media group (album)
    media_group_id: Optional[str] = None

    # Keyboard
    reply_markup: Optional[InlineKeyboardMarkup] = None

    class Config:
        populate_by_name = True

    @property
    def media(self):
        """Xabardagi har qanday mediani qaytaradi — if msg.media: ishlatish uchun"""
        return (
            self.photo
            or self.video
            or self.audio
            or self.document
            or self.voice
            or self.video_note
            or self.sticker
            or self.animation
        )

    @property
    def content_type(self) -> str:
        if self.text:        return "text"
        if self.photo:       return "photo"
        if self.video:       return "video"
        if self.audio:       return "audio"
        if self.document:    return "document"
        if self.voice:       return "voice"
        if self.video_note:  return "video_note"
        if self.sticker:     return "sticker"
        if self.animation:   return "animation"
        if self.location:    return "location"
        if self.contact:     return "contact"
        return "unknown"

    @property
    def is_command(self) -> bool:
        if not self.entities:
            return False
        return any(e.type == "bot_command" for e in self.entities)

    @property
    def command(self) -> Optional[str]:
        if not self.is_command or not self.text:
            return None
        return self.text.split()[0].lstrip("/").split("@")[0]

    @property
    def args(self) -> str:
        if not self.text:
            return ""
        parts = self.text.split(maxsplit=1)
        return parts[1] if len(parts) > 1 else ""


# ─────────────────────────────────────────
# CallbackQuery
# ─────────────────────────────────────────

from pydantic import BaseModel, Field, model_validator

class CallbackQuery(TelegramObject):
    id: str
    from_user: Optional[User] = None
    data: Optional[str] = None
    message: Optional[Message] = None
    chat_instance: str = ""

    @model_validator(mode="before")
    @classmethod
    def parse_from(cls, values):
        if "from" in values:
            values["from_user"] = values.pop("from")
        return values


# ─────────────────────────────────────────
# InlineQuery
# ─────────────────────────────────────────

class InlineQuery(TelegramObject):
    id: str
    from_user: User = Field(alias="from")
    query: str
    offset: str
    chat_type: Optional[str] = None
    location: Optional[Location] = None

    class Config:
        populate_by_name = True


class ChosenInlineResult(TelegramObject):
    result_id: str
    from_user: User = Field(alias="from")
    query: str
    inline_message_id: Optional[str] = None
    location: Optional[Location] = None

    class Config:
        populate_by_name = True


# ─────────────────────────────────────────
# Poll
# ─────────────────────────────────────────

class PollOption(TelegramObject):
    text: str
    voter_count: int


class Poll(TelegramObject):
    id: str
    question: str
    options: List[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str  # regular | quiz
    allows_multiple_answers: bool
    correct_option_id: Optional[int] = None


class PollAnswer(TelegramObject):
    poll_id: str
    user: User
    option_ids: List[int]


# ─────────────────────────────────────────
# Chat Member
# ─────────────────────────────────────────

class ChatMemberUpdated(TelegramObject):
    chat: Chat
    from_user: User = Field(alias="from")
    date: int
    old_chat_member: dict
    new_chat_member: dict

    class Config:
        populate_by_name = True


# ─────────────────────────────────────────
# Chat Join Request
# ─────────────────────────────────────────

class ChatJoinRequest(TelegramObject):
    chat: Chat
    from_user: User = Field(alias="from")
    date: int
    bio: Optional[str] = None
    invite_link: Optional[dict] = None

    class Config:
        populate_by_name = True


# ─────────────────────────────────────────
# Update  — "Aqlli Konteyner"
# ─────────────────────────────────────────

class Update(TelegramObject):
    update_id: int

    # Asosiy
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    inline_query: Optional[InlineQuery] = None
    chosen_inline_result: Optional[ChosenInlineResult] = None

    # Kengaytirilgan
    poll: Optional[Poll] = None
    poll_answer: Optional[PollAnswer] = None
    my_chat_member: Optional[ChatMemberUpdated] = None
    chat_member: Optional[ChatMemberUpdated] = None
    chat_join_request: Optional[ChatJoinRequest] = None

    @property
    def event_type(self) -> str:
        """Qaysi turdagi update ekanini aniqlaydi"""
        if self.message:               return "message"
        if self.edited_message:        return "edited_message"
        if self.channel_post:          return "channel_post"
        if self.callback_query:        return "callback_query"
        if self.inline_query:          return "inline_query"
        if self.chosen_inline_result:  return "chosen_inline_result"
        if self.poll:                  return "poll"
        if self.poll_answer:           return "poll_answer"
        if self.my_chat_member:        return "my_chat_member"
        if self.chat_member:           return "chat_member"
        if self.chat_join_request:     return "chat_join_request"
        return "unknown"

    @property
    def effective_message(self) -> Optional[Message]:
        """message yoki edited_message yoki channel_post — qaysi bo'lsa"""
        return self.message or self.edited_message or self.channel_post

    @property
    def effective_user(self) -> Optional[User]:
        if self.message:              return self.message.from_user
        if self.edited_message:       return self.edited_message.from_user
        if self.callback_query:       return self.callback_query.from_user
        if self.inline_query:         return self.inline_query.from_user
        if self.poll_answer:          return self.poll_answer.user
        if self.my_chat_member:       return self.my_chat_member.from_user
        if self.chat_join_request:    return self.chat_join_request.from_user
        return None

    @property
    def effective_chat(self) -> Optional[Chat]:
        if self.message:              return self.message.chat
        if self.edited_message:       return self.edited_message.chat
        if self.callback_query and self.callback_query.message:
            return self.callback_query.message.chat
        if self.my_chat_member:       return self.my_chat_member.chat
        if self.chat_join_request:    return self.chat_join_request.chat
        return None


# Forward reference resolve
Message.model_rebuild()