from app.common.schema import CamelModel
from app.features.import_forms.models import ImportForm


class ExtractedQuestionDto(CamelModel):
    text_en: str
    text_ar: str
    answer_type: str


class ImportDto(CamelModel):
    id: str
    status: str
    source_file_name: str
    question_count: int
    questions: list[ExtractedQuestionDto]
    used_fallback: bool

    @classmethod
    def from_model(cls, record: ImportForm) -> "ImportDto":
        return cls(
            id=str(record.id),
            status=record.status,
            source_file_name=record.source_file_name,
            question_count=record.question_count,
            questions=[
                ExtractedQuestionDto(
                    text_en=q["textEn"], text_ar=q["textAr"], answer_type=q["answerType"]
                )
                for q in record.questions
            ],
            used_fallback=record.used_fallback,
        )


class IntakeFormDefinitionDto(CamelModel):
    """Reference the intake screen consumes to render the imported questions (FR-IMP-3)."""

    import_id: str
    question_count: int
    questions: list[ExtractedQuestionDto]
