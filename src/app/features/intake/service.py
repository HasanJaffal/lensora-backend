import uuid

from app.common.envelope import ErrorDetail
from app.common.exceptions import NotFoundError, ValidationError
from app.features.intake.models import IntakeStatus, IntakeSubmission
from app.features.intake.repository import IntakeRepository
from app.features.intake.schemas import (
    IndividualInfoDto,
    IntakeCreateRequest,
    IntakeDto,
    IntakeListItemDto,
    IntakeUpdateRequest,
    MotiveDto,
)


class IntakeService:
    """Business logic for intake questionnaires: draft/complete lifecycle (FR-INT)."""

    def __init__(self, intakes: IntakeRepository) -> None:
        self._intakes = intakes

    async def create_intake(self, request: IntakeCreateRequest) -> IntakeDto:
        if request.status is IntakeStatus.COMPLETED:
            _validate_completion(request.individual_info, request.motive)

        intake = IntakeSubmission(
            status=request.status.value,
            patient_id=request.patient_id,
            individual_info=request.individual_info.model_dump(mode="json"),
            motive=request.motive.model_dump(mode="json"),
            themes=request.themes.model_dump(mode="json"),
            refraction_history=request.refraction_history.model_dump(mode="json"),
            antecedents=request.antecedents.model_dump(mode="json"),
        )
        self._intakes.add(intake)
        await self._intakes.commit()
        await self._intakes.refresh(intake)
        return IntakeDto.from_model(intake)

    async def get_intake(self, intake_id: uuid.UUID) -> IntakeDto:
        return IntakeDto.from_model(await self._require_intake(intake_id))

    async def list_intakes(
        self, *, patient_id: uuid.UUID | None, status: IntakeStatus | None
    ) -> list[IntakeListItemDto]:
        records = await self._intakes.list_submissions(
            patient_id=patient_id, status=status
        )
        return [IntakeListItemDto.from_model(record) for record in records]

    async def update_intake(
        self, intake_id: uuid.UUID, request: IntakeUpdateRequest
    ) -> IntakeDto:
        intake = await self._require_intake(intake_id)
        changed = request.model_fields_set

        if "patient_id" in changed:
            intake.patient_id = request.patient_id
        if request.individual_info is not None:
            intake.individual_info = request.individual_info.model_dump(mode="json")
        if request.motive is not None:
            intake.motive = request.motive.model_dump(mode="json")
        if request.themes is not None:
            intake.themes = request.themes.model_dump(mode="json")
        if request.refraction_history is not None:
            intake.refraction_history = request.refraction_history.model_dump(mode="json")
        if request.antecedents is not None:
            intake.antecedents = request.antecedents.model_dump(mode="json")

        target_status = request.status.value if request.status is not None else intake.status
        if target_status == IntakeStatus.COMPLETED:
            _validate_completion(
                IndividualInfoDto.model_validate(intake.individual_info),
                MotiveDto.model_validate(intake.motive),
            )
        intake.status = target_status

        await self._intakes.commit()
        await self._intakes.refresh(intake)
        return IntakeDto.from_model(intake)

    async def _require_intake(self, intake_id: uuid.UUID) -> IntakeSubmission:
        intake = await self._intakes.get_by_id(intake_id)
        if intake is None:
            raise NotFoundError(f"Intake {intake_id} not found")
        return intake


def _validate_completion(individual_info: IndividualInfoDto, motive: MotiveDto) -> None:
    missing = [
        ErrorDetail(field=field, message="Required to complete the intake")
        for field, value in (
            ("individualInfo.name", individual_info.name),
            ("individualInfo.birthdate", individual_info.birthdate),
            ("motive.reasonForVisit", motive.reason_for_visit),
        )
        if not value
    ]
    if missing:
        raise ValidationError("Intake is missing required fields", details=missing)
