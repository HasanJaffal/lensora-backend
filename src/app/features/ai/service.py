from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.envelope import ErrorDetail
from app.common.exceptions import PatientNotFoundError, ValidationError
from app.common.tenant_context import TenantContext
from app.features.ai.context import (
    AssistantContext,
    FrameSummary,
    PatientSummary,
    StockSummary,
    StylingContext,
)
from app.features.ai.provider import AIProvider, FallbackProvider
from app.features.ai.schemas import (
    ChatMessage,
    ChatResponseDto,
    Locale,
    StylingAdviceDto,
    StylingAdviceRequest,
)
from app.features.inventory.repository import InventoryRepository
from app.features.inventory.status import derive_stock_status
from app.features.patients.models import Patient
from app.features.patients.repository import PatientRepository

_MAX_CONTEXT_PATIENTS = 20

_SUGGESTIONS: dict[Locale, list[str]] = {
    Locale.EN: [
        "Which items are low on stock?",
        "What is Layla Haidar's prescription?",
        "Best lens for heavy screen use?",
    ],
    Locale.AR: [
        "ما هي الأصناف المنخفضة في المخزون؟",
        "ما هي وصفة ليلى حيدر؟",
        "أفضل عدسة للاستخدام الكثيف للشاشة؟",
    ],
}


class AIService:
    """Grounded chat and styling advice with a deterministic fallback (NFR-4 / FR-AI)."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_context: TenantContext,
        provider: AIProvider,
        fallback: FallbackProvider,
    ) -> None:
        self._session = session
        self._tenant_context = tenant_context
        self._provider = provider
        self._fallback = fallback

    async def chat(self, messages: list[ChatMessage], locale: Locale) -> ChatResponseDto:
        context = await self._assemble_context()
        try:
            content = await self._provider.chat(messages, context, locale)
            used_fallback = isinstance(self._provider, FallbackProvider)
        except Exception:
            content = await self._fallback.chat(messages, context, locale)
            used_fallback = True
        return ChatResponseDto(
            message=ChatMessage(role="assistant", content=content),
            used_fallback=used_fallback,
        )

    def suggestions(self, locale: Locale) -> list[str]:
        return _SUGGESTIONS[locale]

    async def styling_advice(self, request: StylingAdviceRequest) -> StylingAdviceDto:
        context = await self._assemble_styling_context(request)
        try:
            tips = await self._provider.styling_advice(context, request.locale)
            used_fallback = isinstance(self._provider, FallbackProvider)
        except Exception:
            tips = await self._fallback.styling_advice(context, request.locale)
            used_fallback = True
        return StylingAdviceDto(tips=tips, used_fallback=used_fallback)

    async def _assemble_context(self) -> AssistantContext:
        patients = PatientRepository(self._session, self._tenant_context)
        inventory = InventoryRepository(self._session, self._tenant_context)
        records, _ = await patients.list_page(
            status=None, query=None, offset=0, limit=_MAX_CONTEXT_PATIENTS
        )
        low_stock_items = await inventory.list_items(low_stock=True)
        return AssistantContext(
            patients=[_patient_summary(record) for record in records],
            low_stock=[
                StockSummary(
                    name=item.name,
                    sku=item.sku,
                    quantity=item.quantity,
                    status=derive_stock_status(item.quantity, item.threshold),
                )
                for item in low_stock_items
            ],
        )

    async def _assemble_styling_context(self, request: StylingAdviceRequest) -> StylingContext:
        inventory = InventoryRepository(self._session, self._tenant_context)
        frame = await inventory.get_by_id(request.frame_id)
        if frame is None:
            raise ValidationError(
                "Unknown frame",
                details=[ErrorDetail(field="frameId", message="Unknown frame")],
            )

        diagnosis: str | None = None
        if request.patient_id is not None:
            patient = await PatientRepository(self._session, self._tenant_context).get_by_id(
                request.patient_id
            )
            if patient is None:
                raise PatientNotFoundError(f"Patient {request.patient_id} not found")
            diagnosis = patient.diagnosis_en

        return StylingContext(
            frame=FrameSummary(
                name=frame.name,
                brand=frame.brand,
                shape=frame.shape,
                color=frame.color,
            ),
            need=request.need.value,
            diagnosis=diagnosis,
        )


def _patient_summary(patient: Patient) -> PatientSummary:
    return PatientSummary(
        name=patient.name_en,
        town=patient.town_en,
        age=date.today().year - patient.birth_year,
        status=patient.status,
        diagnosis=patient.diagnosis_en,
        od_sph=str(patient.od_sph) if patient.od_sph is not None else None,
        os_sph=str(patient.os_sph) if patient.os_sph is not None else None,
    )
