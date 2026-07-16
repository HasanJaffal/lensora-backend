from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, TenantContextDep, require_auth
from app.common.envelope import Envelope, ok
from app.features.ai.deps import get_ai_provider, get_fallback_provider
from app.features.ai.schemas import (
    ChatRequest,
    ChatResponseDto,
    ChatSuggestionsDto,
    Locale,
    StylingAdviceDto,
    StylingAdviceRequest,
)
from app.features.ai.service import AIService

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_auth)])


def get_ai_service(session: SessionDep, tenant_context: TenantContextDep) -> AIService:
    return AIService(session, tenant_context, get_ai_provider(), get_fallback_provider())


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]


@router.post("/chat")
async def chat(body: ChatRequest, service: AIServiceDep) -> Envelope[ChatResponseDto]:
    return ok(await service.chat(body.messages, body.locale))


@router.get("/chat/suggestions")
async def chat_suggestions(
    service: AIServiceDep,
    locale: Annotated[Locale, Query()] = Locale.EN,
) -> Envelope[ChatSuggestionsDto]:
    return ok(ChatSuggestionsDto(suggestions=service.suggestions(locale)))


@router.post("/styling-advice")
async def styling_advice(
    body: StylingAdviceRequest, service: AIServiceDep
) -> Envelope[StylingAdviceDto]:
    return ok(await service.styling_advice(body))
