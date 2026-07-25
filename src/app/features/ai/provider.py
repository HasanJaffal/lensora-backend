import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.features.ai.context import AssistantContext, StylingContext
from app.features.ai.schemas import ChatMessage, Locale

if TYPE_CHECKING:
    from google.genai.types import Content, GenerateContentResponse

AnswerType = str  # one of: "short" | "long" | "checklist"

_MAX_WORDS = 80


@dataclass(frozen=True)
class ExtractedQuestion:
    text_en: str
    text_ar: str
    answer_type: AnswerType


class AIProvider(ABC):
    """Contract shared by the Gemini client and its deterministic fallback.

    Feature code depends on this abstraction, never a concrete client, so every method has a
    counterpart in :class:`FallbackProvider` and the workflow never blocks (NFR-4).
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


class GeminiProvider(AIProvider):
    """Real provider backed by Gemini via the google-genai SDK."""

    def __init__(self, *, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def chat(
        self, messages: list[ChatMessage], context: AssistantContext, locale: Locale
    ) -> str:
        conversation = [_chat_turn(message) for message in messages]
        return await self._generate(
            contents=conversation,
            system_instruction=_chat_system_prompt(context, locale),
            max_output_tokens=400,
        )

    async def styling_advice(self, context: StylingContext, locale: Locale) -> list[str]:
        text = await self._generate(
            contents=[_user_turn(_styling_user_prompt(context))],
            system_instruction=_styling_system_prompt(locale),
            max_output_tokens=400,
        )
        tips = [line.strip("-• ").strip() for line in text.splitlines()]
        return [tip for tip in tips if tip][:3]

    async def extract_questions(
        self, document: bytes, filename: str, content_type: str
    ) -> list[ExtractedQuestion]:
        from google.genai import types

        document_turn = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=document, mime_type=content_type),
                types.Part.from_text(text=_EXTRACTION_INSTRUCTION),
            ],
        )
        text = await self._generate(
            contents=[document_turn],
            system_instruction=_EXTRACTION_SYSTEM_PROMPT,
            max_output_tokens=2000,
            response_mime_type="application/json",
        )
        return _parse_extracted_questions(text)

    async def _generate(
        self,
        *,
        contents: list["Content"],
        system_instruction: str,
        max_output_tokens: int,
        response_mime_type: str | None = None,
    ) -> str:
        from google.genai import types

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_output_tokens,
                response_mime_type=response_mime_type,
                # Flash models reason by default, which would spend the token budget before any
                # answer text is emitted; these prompts need the output, not the reasoning.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return _response_text(response)


def _chat_turn(message: ChatMessage) -> "Content":
    # Gemini names the assistant side of a conversation "model", not "assistant".
    return _turn("user" if message.role == "user" else "model", message.content)


def _user_turn(text: str) -> "Content":
    return _turn("user", text)


def _turn(role: str, text: str) -> "Content":
    from google.genai import types

    return types.Content(role=role, parts=[types.Part.from_text(text=text)])


def _response_text(response: "GenerateContentResponse") -> str:
    text = response.text
    if not text or not text.strip():
        raise ValueError("AI response contained no text")
    return text.strip()


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
