import uuid
from enum import StrEnum
from typing import Literal

from pydantic import Field

from app.common.schema import CamelModel


class Locale(StrEnum):
    EN = "en"
    AR = "ar"


class ProductNeed(StrEnum):
    EYEGLASSES = "eyeglasses"
    SUNGLASSES = "sunglasses"
    CONTACTS = "contacts"


class ChatMessage(CamelModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(CamelModel):
    messages: list[ChatMessage] = Field(min_length=1)
    locale: Locale = Locale.EN


class ChatResponseDto(CamelModel):
    message: ChatMessage
    used_fallback: bool


class ChatSuggestionsDto(CamelModel):
    suggestions: list[str]


class StylingAdviceRequest(CamelModel):
    patient_id: uuid.UUID | None = None
    frame_id: uuid.UUID
    need: ProductNeed = ProductNeed.EYEGLASSES
    locale: Locale = Locale.EN


class StylingAdviceDto(CamelModel):
    tips: list[str]
    used_fallback: bool
