import base64
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from app.features.ai.context import AssistantContext, StylingContext
from app.features.ai.schemas import ChatMessage, Locale

if TYPE_CHECKING:
    from anthropic.types import (
        ContentBlockParam,
        Message,
        MessageParam,
        ThinkingConfigDisabledParam,
    )

AnswerType = str  # one of: "short" | "long" | "checklist"

_MAX_WORDS = 80


@dataclass(frozen=True)
class ExtractedQuestion:
    text_en: str
    text_ar: str
    answer_type: AnswerType


class AIProvider(ABC):
    """Swappable AI strategy (Open/Closed, Liskov-substitutable).

    Feature code depends on this abstraction, never a concrete client. Every method has a
    deterministic counterpart in :class:`FallbackProvider` so the workflow never blocks (NFR-4).
    """

    @abstractmethod
    async def chat(
        self, messages: list[ChatMessage], context: AssistantContext, locale: Locale
    ) -> str: ...

    @abstractmethod
    async def styling_advice(self, context: StylingContext, locale: Locale) -> list[str]: ...

    @abstractmethod
    async def extract_questions(
        self, document: bytes, filename: str, content_type: str
    ) -> list[ExtractedQuestion]: ...


class FallbackProvider(AIProvider):
    """Deterministic static content used when no AI service is configured or on error."""

    async def chat(
        self, messages: list[ChatMessage], context: AssistantContext, locale: Locale
    ) -> str:
        low = len(context.low_stock)
        in_lab = sum(1 for patient in context.patients if patient.status == "lab")
        if locale is Locale.AR:
            return (
                "المساعد الذكي غير متصل حالياً، لكن يمكنني رؤية بياناتك: "
                f"{low} صنف منخفض المخزون و{in_lab} مريض في المختبر. "
                "حاول مجدداً عند عودة الخدمة."
            )
        return (
            "The AI assistant is offline right now, but here is what I can see in your data: "
            f"{low} item(s) are low on stock and {in_lab} patient(s) are in the lab. "
            "Please try again when the service is back online."
        )

    async def styling_advice(self, context: StylingContext, locale: Locale) -> list[str]:
        shape = context.frame.shape or "classic"
        if locale is Locale.AR:
            return [
                f"إطار {shape} خيار متعدد الاستخدامات يناسب معظم ملامح الوجه.",
                "تأكد من أن عرض الإطار يوازي عرض الوجه لإطلالة متوازنة.",
                "للاستخدام أمام الشاشة، أضف طلاءً مضاداً للانعكاس لراحة أكبر.",
            ]
        return [
            f"A {shape} frame is a versatile choice that suits most face shapes.",
            "Pick a frame whose width matches the face width for a balanced look.",
            "For screen work, pair it with an anti-reflective coating for comfort.",
        ]

    async def extract_questions(
        self, document: bytes, filename: str, content_type: str
    ) -> list[ExtractedQuestion]:
        return list(_FALLBACK_QUESTIONS)


_THINKING_OFF: "ThinkingConfigDisabledParam" = {"type": "disabled"}


class AnthropicProvider(AIProvider):
    """Real provider backed by the latest Claude Sonnet model via the Anthropic SDK."""

    def __init__(self, *, api_key: str, model: str) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def chat(
        self, messages: list[ChatMessage], context: AssistantContext, locale: Locale
    ) -> str:
        conversation: list[MessageParam] = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=400,
            thinking=_THINKING_OFF,
            system=_chat_system_prompt(context, locale),
            messages=conversation,
        )
        return _first_text(response)

    async def styling_advice(self, context: StylingContext, locale: Locale) -> list[str]:
        conversation: list[MessageParam] = [
            {"role": "user", "content": _styling_user_prompt(context)}
        ]
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=400,
            thinking=_THINKING_OFF,
            system=_styling_system_prompt(locale),
            messages=conversation,
        )
        tips = [line.strip("-• ").strip() for line in _first_text(response).splitlines()]
        return [tip for tip in tips if tip][:3]

    async def extract_questions(
        self, document: bytes, filename: str, content_type: str
    ) -> list[ExtractedQuestion]:
        content: list[ContentBlockParam] = [
            _document_block(document, content_type),
            {"type": "text", "text": _EXTRACTION_INSTRUCTION},
        ]
        conversation: list[MessageParam] = [{"role": "user", "content": content}]
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            thinking=_THINKING_OFF,
            system=_EXTRACTION_SYSTEM_PROMPT,
            messages=conversation,
        )
        return _parse_extracted_questions(_first_text(response))


def _first_text(response: "Message") -> str:
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError("AI response contained no text block")


def _chat_system_prompt(context: AssistantContext, locale: Locale) -> str:
    lines = [
        "You are the practice assistant for Lensora, an optometry clinic.",
        f"Answer in {'Arabic' if locale is Locale.AR else 'English'} unless asked otherwise.",
        f"Keep answers concise — at most {_MAX_WORDS} words.",
        "Use the practice data below when relevant; do not invent patients or stock.",
        "",
        "Patients:",
    ]
    lines += [
        f"- {p.name} ({p.town}, age {p.age}, status {p.status}): "
        f"{p.diagnosis or 'no diagnosis'}; OD sph {p.od_sph}, OS sph {p.os_sph}"
        for p in context.patients
    ] or ["- (none)"]
    lines.append("Low/out-of-stock items:")
    lines += [
        f"- {item.name} ({item.sku}): {item.quantity} left, {item.status}"
        for item in context.low_stock
    ] or ["- (none)"]
    return "\n".join(lines)


def _styling_system_prompt(locale: Locale) -> str:
    language = "Arabic" if locale is Locale.AR else "English"
    return (
        "You are an optical stylist. Give 2-3 short, practical tips on whether the frame "
        f"suits the patient, considering face-shape fit and lens pairing. Answer in {language}. "
        "Return each tip on its own line, no numbering."
    )


def _styling_user_prompt(context: StylingContext) -> str:
    return (
        f"Frame: {context.frame.brand} {context.frame.name}, shape {context.frame.shape}, "
        f"color {context.frame.color}. Need: {context.need}. "
        f"Patient diagnosis: {context.diagnosis or 'not provided'}."
    )


_EXTRACTION_SYSTEM_PROMPT = (
    "You extract questions from a scanned intake or questionnaire form. "
    "For each question, classify its answer type as one of: short, long, checklist."
)

_EXTRACTION_INSTRUCTION = (
    "List every question in the document. Respond ONLY with a JSON array of objects with keys "
    '"textEn", "textAr", "answerType" (short|long|checklist). Translate each question into both '
    "English and Arabic."
)


def _document_block(document: bytes, content_type: str) -> "ContentBlockParam":
    data = base64.standard_b64encode(document).decode("ascii")
    is_pdf = content_type == "application/pdf"
    # Single boundary cast: content_type is a runtime-validated PDF/image MIME string,
    # while the SDK types media_type as a closed Literal.
    return cast(
        "ContentBlockParam",
        {
            "type": "document" if is_pdf else "image",
            "source": {"type": "base64", "media_type": content_type, "data": data},
        },
    )


def _parse_extracted_questions(payload: str) -> list[ExtractedQuestion]:
    start, end = payload.find("["), payload.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("AI extraction response was not a JSON array")
    items = json.loads(payload[start : end + 1])
    questions = [
        ExtractedQuestion(
            text_en=str(item["textEn"]),
            text_ar=str(item["textAr"]),
            answer_type=str(item["answerType"]),
        )
        for item in items
        if item.get("answerType") in ("short", "long", "checklist")
    ]
    if not questions:
        raise ValueError("AI extraction returned no valid questions")
    return questions


_FALLBACK_QUESTIONS: tuple[ExtractedQuestion, ...] = (
    ExtractedQuestion("Full name", "الاسم الكامل", "short"),
    ExtractedQuestion("Date of birth", "تاريخ الميلاد", "short"),
    ExtractedQuestion("Reason for today's visit", "سبب زيارة اليوم", "long"),
    ExtractedQuestion(
        "Which visual problems are you experiencing?",
        "ما هي المشاكل البصرية التي تعاني منها؟",
        "checklist",
    ),
    ExtractedQuestion(
        "Do you have any relevant medical history?",
        "هل لديك أي تاريخ طبي ذي صلة؟",
        "long",
    ),
)
