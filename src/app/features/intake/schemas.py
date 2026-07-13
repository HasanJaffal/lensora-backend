import uuid
from datetime import date, datetime

from pydantic import Field

from app.common.schema import CamelModel
from app.features.intake.enums import (
    CorrectionPreference,
    FunctionalSign,
    Gender,
    Onset,
    VisualProblem,
)
from app.features.intake.models import IntakeStatus, IntakeSubmission


class IndividualInfoDto(CamelModel):
    name: str | None = None
    form_date: date | None = None
    address: str | None = None
    home_phone: str | None = None
    city: str | None = None
    cell_phone: str | None = None
    email: str | None = None
    birthdate: date | None = None
    gender: Gender | None = None
    last_eye_exam_date: date | None = None
    profession: str | None = None
    hobbies: str | None = None


class MotiveDto(CamelModel):
    reason_for_visit: str | None = None
    visual_problems: list[VisualProblem] = Field(default_factory=list)
    functional_signs: list[FunctionalSign] = Field(default_factory=list)


class ThemesDto(CamelModel):
    onset: Onset | None = None
    timing: str | None = None
    time_of_day: str | None = None
    context: str | None = None
    correction_state: str | None = None
    associated_complaints: str | None = None
    first_occurrence: str | None = None
    trend: str | None = None
    permanence: str | None = None
    relief_measures: str | None = None


class EyewearHistoryDto(CamelModel):
    wears: bool | None = None
    wear_history: str | None = None
    activity: str | None = None
    last_prescription_date: date | None = None
    last_acuity: str | None = None
    correction_value: str | None = None
    centering: str | None = None
    satisfaction: str | None = None
    lens_type: str | None = None
    brand: str | None = None
    wear_frequency: str | None = None


class RefractionHistoryDto(CamelModel):
    eyeglasses: EyewearHistoryDto = Field(default_factory=EyewearHistoryDto)
    contact_lenses: EyewearHistoryDto = Field(default_factory=EyewearHistoryDto)
    overall_preference: CorrectionPreference | None = None


class OcularHistoryDto(CamelModel):
    pathology: str | None = None
    surgery: str | None = None
    trauma: str | None = None
    orthoptic_treatment: str | None = None


class GeneralHealthDto(CamelModel):
    diabetes: bool | None = None
    hypertension: bool | None = None
    other: str | None = None


class FamilyHistoryDto(CamelModel):
    refractive: str | None = None
    pathological: str | None = None
    relationship: str | None = None


class AntecedentsDto(CamelModel):
    ocular_history: OcularHistoryDto = Field(default_factory=OcularHistoryDto)
    general_health: GeneralHealthDto = Field(default_factory=GeneralHealthDto)
    medication: str | None = None
    family_history: FamilyHistoryDto = Field(default_factory=FamilyHistoryDto)


class IntakeDto(CamelModel):
    id: str
    status: str
    patient_id: str | None
    individual_info: IndividualInfoDto
    motive: MotiveDto
    themes: ThemesDto
    refraction_history: RefractionHistoryDto
    antecedents: AntecedentsDto
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, intake: IntakeSubmission) -> "IntakeDto":
        return cls(
            id=str(intake.id),
            status=intake.status,
            patient_id=str(intake.patient_id) if intake.patient_id else None,
            individual_info=IndividualInfoDto.model_validate(intake.individual_info),
            motive=MotiveDto.model_validate(intake.motive),
            themes=ThemesDto.model_validate(intake.themes),
            refraction_history=RefractionHistoryDto.model_validate(
                intake.refraction_history
            ),
            antecedents=AntecedentsDto.model_validate(intake.antecedents),
            created_at=intake.created_at,
            updated_at=intake.updated_at,
        )


class IntakeListItemDto(CamelModel):
    id: str
    status: str
    patient_id: str | None
    name: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, intake: IntakeSubmission) -> "IntakeListItemDto":
        return cls(
            id=str(intake.id),
            status=intake.status,
            patient_id=str(intake.patient_id) if intake.patient_id else None,
            name=intake.individual_info.get("name"),
            created_at=intake.created_at,
            updated_at=intake.updated_at,
        )


class IntakeCreateRequest(CamelModel):
    status: IntakeStatus = IntakeStatus.DRAFT
    patient_id: uuid.UUID | None = None
    individual_info: IndividualInfoDto = Field(default_factory=IndividualInfoDto)
    motive: MotiveDto = Field(default_factory=MotiveDto)
    themes: ThemesDto = Field(default_factory=ThemesDto)
    refraction_history: RefractionHistoryDto = Field(
        default_factory=RefractionHistoryDto
    )
    antecedents: AntecedentsDto = Field(default_factory=AntecedentsDto)


class IntakeUpdateRequest(CamelModel):
    status: IntakeStatus | None = None
    patient_id: uuid.UUID | None = None
    individual_info: IndividualInfoDto | None = None
    motive: MotiveDto | None = None
    themes: ThemesDto | None = None
    refraction_history: RefractionHistoryDto | None = None
    antecedents: AntecedentsDto | None = None
