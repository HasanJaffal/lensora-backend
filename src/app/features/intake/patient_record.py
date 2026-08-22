from datetime import date

from pydantic import BaseModel, Field
from pydantic import ValidationError as SchemaValidationError

from app.common.envelope import ErrorDetail
from app.common.exceptions import ValidationError
from app.features.intake.schemas import IndividualInfoDto, MotiveDto
from app.features.patients.models import Patient, PatientStatus

_MISSING_ANSWER_MESSAGE = "Required to complete the intake"
_ANSWER_FIELD_PATHS = {
    "name": "individualInfo.name",
    "birthdate": "individualInfo.birthdate",
    "city": "individualInfo.city",
    "cell_phone": "individualInfo.cellPhone",
    "reason_for_visit": "motive.reasonForVisit",
}


class CompletedIntakeAnswers(BaseModel):
    """The answers a completed intake must carry to open a patient record (FR-INT-2)."""

    name: str = Field(min_length=1)
    birthdate: date
    city: str = Field(min_length=1)
    cell_phone: str = Field(min_length=1)
    reason_for_visit: str = Field(min_length=1)


def require_completed_answers(
    individual_info: IndividualInfoDto, motive: MotiveDto
) -> CompletedIntakeAnswers:
    try:
        return CompletedIntakeAnswers.model_validate(
            {
                "name": _trimmed(individual_info.name),
                "birthdate": individual_info.birthdate,
                "city": _trimmed(individual_info.city),
                "cell_phone": _trimmed(individual_info.cell_phone),
                "reason_for_visit": _trimmed(motive.reason_for_visit),
            }
        )
    except SchemaValidationError as exc:
        raise ValidationError(
            "Intake is missing required fields", details=_missing_answer_details(exc)
        ) from exc


def build_patient_record(answers: CompletedIntakeAnswers, visit_date: date | None) -> Patient:
    # The intake captures one name and one city, so both language columns start from that answer.
    return Patient(
        name_en=answers.name,
        name_ar=answers.name,
        phone=answers.cell_phone,
        town_en=answers.city,
        town_ar=answers.city,
        birth_year=answers.birthdate.year,
        status=PatientStatus.ACTIVE.value,
        last_visit=visit_date or date.today(),
    )


def _trimmed(value: str | None) -> str:
    return value.strip() if value is not None else ""


def _missing_answer_details(exc: SchemaValidationError) -> list[ErrorDetail]:
    details: list[ErrorDetail] = []
    for error in exc.errors():
        location = error["loc"]
        field_path = _ANSWER_FIELD_PATHS.get(str(location[0])) if location else None
        if field_path is not None:
            details.append(ErrorDetail(field=field_path, message=_MISSING_ANSWER_MESSAGE))
    return details
