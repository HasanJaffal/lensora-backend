import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from app.common.tenant_context import TenantContext
from app.features.ai.provider import AIProvider, ExtractedQuestion, FallbackProvider
from app.features.import_forms.models import ImportForm, ImportStatus
from app.features.import_forms.repository import ImportRepository
from app.features.import_forms.schemas import (
    ExtractedQuestionDto,
    ImportDto,
    IntakeFormDefinitionDto,
)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
_ALLOWED_CONTENT_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png"})


class ImportService:
    """Upload-and-extract flow for paper forms with a deterministic fallback (FR-IMP / NFR-4)."""

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

    async def create_import(self, *, filename: str, content_type: str, data: bytes) -> ImportDto:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise UnsupportedMediaTypeError(
                f"Unsupported file type '{content_type}'; expected PDF, JPEG, or PNG"
            )
        if len(data) > MAX_FILE_SIZE_BYTES:
            raise PayloadTooLargeError("File exceeds the 20 MB limit")

        questions, used_fallback = await self._extract(data, filename, content_type)
        record = ImportForm(
            status=ImportStatus.READY.value,
            source_file_name=filename,
            question_count=len(questions),
            questions=[_to_dict(q) for q in questions],
            used_fallback=used_fallback,
        )
        repository = ImportRepository(self._session, self._tenant_context)
        repository.add(record)
        await repository.commit()
        await repository.refresh(record)
        return ImportDto.from_model(record)

    async def get_import(self, import_id: uuid.UUID) -> ImportDto:
        return ImportDto.from_model(await self._require_import(import_id))

    async def use_as_intake(self, import_id: uuid.UUID) -> IntakeFormDefinitionDto:
        record = await self._require_import(import_id)
        return IntakeFormDefinitionDto(
            import_id=str(record.id),
            question_count=record.question_count,
            questions=[
                ExtractedQuestionDto(
                    text_en=q["textEn"], text_ar=q["textAr"], answer_type=q["answerType"]
                )
                for q in record.questions
            ],
        )

    async def _extract(
        self, data: bytes, filename: str, content_type: str
    ) -> tuple[list[ExtractedQuestion], bool]:
        try:
            questions = await self._provider.extract_questions(data, filename, content_type)
            return questions, isinstance(self._provider, FallbackProvider)
        except Exception:
            return await self._fallback.extract_questions(data, filename, content_type), True

    async def _require_import(self, import_id: uuid.UUID) -> ImportForm:
        record = await ImportRepository(self._session, self._tenant_context).get_by_id(import_id)
        if record is None:
            raise NotFoundError(f"Import {import_id} not found")
        return record


def _to_dict(question: ExtractedQuestion) -> dict[str, str]:
    return {
        "textEn": question.text_en,
        "textAr": question.text_ar,
        "answerType": question.answer_type,
    }
