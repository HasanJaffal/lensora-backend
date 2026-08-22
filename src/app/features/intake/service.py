import uuid
from datetime import date

from app.common.exceptions import NotFoundError
from app.features.intake.models import IntakeStatus, IntakeSubmission
from app.features.intake.patient_record import (
    CompletedIntakeAnswers,
    build_patient_record,
    require_completed_answers,
)
from app.features.intake.repository import IntakeRepository
from app.features.intake.schemas import (
    IndividualInfoDto,
    IntakeCreateRequest,
    IntakeDto,
    IntakeListItemDto,
    IntakeUpdateRequest,
    MotiveDto,
)
from app.features.patients.repository import PatientRepository


class IntakeService:
    """Business logic for intake questionnaires: draft/complete lifecycle (FR-INT)."""

    def __init__(self, intakes: IntakeRepository, patients: PatientRepository) -> None:
        self._intakes = intakes
        self._patients = patients

    async def create_intake(self, request: IntakeCreateRequest) -> IntakeDto:
        intake = IntakeSubmission(
            status=request.status.value,
            patient_id=request.patient_id,
            individual_info=request.individual_info.model_dump(mode="json"),
            motive=request.motive.model_dump(mode="json"),
            themes=request.themes.model_dump(mode="json"),
            refraction_history=request.refraction_history.model_dump(mode="json"),
            antecedents=request.antecedents.model_dump(mode="json"),
        )

        if request.status is IntakeStatus.COMPLETED:
            answers = require_completed_answers(request.individual_info, request.motive)
            await self._link_patient_record(intake, answers, request.individual_info.form_date)

        self._intakes.add(intake)
        await self._intakes.commit()
        await self._intakes.refresh(intake)
        return IntakeDto.from_model(intake)

    async def get_intake(self, intake_id: uuid.UUID) -> IntakeDto:
        return IntakeDto.from_model(await self._require_intake(intake_id))

    async def list_intakes(
        self, *, patient_id: uuid.UUID | None, status: IntakeStatus | None
    ) -> list[IntakeListItemDto]:
        records = await self._intakes.list_submissions(patient_id=patient_id, status=status)
        return [IntakeListItemDto.from_model(record) for record in records]

    async def update_intake(self, intake_id: uuid.UUID, request: IntakeUpdateRequest) -> IntakeDto:
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
            individual_info = IndividualInfoDto.model_validate(intake.individual_info)
            answers = require_completed_answers(
                individual_info, MotiveDto.model_validate(intake.motive)
            )
            await self._link_patient_record(intake, answers, individual_info.form_date)
        intake.status = target_status

        await self._intakes.commit()
        await self._intakes.refresh(intake)
        return IntakeDto.from_model(intake)

    async def _link_patient_record(
        self,
        intake: IntakeSubmission,
        answers: CompletedIntakeAnswers,
        visit_date: date | None,
    ) -> None:
        """Open the patient record a completed intake stands for, unless one is already linked."""
        if intake.patient_id is not None:
            return

        patient = build_patient_record(answers, visit_date)
        self._patients.add(patient)
        await self._patients.flush()
        intake.patient_id = patient.id

    async def _require_intake(self, intake_id: uuid.UUID) -> IntakeSubmission:
        intake = await self._intakes.get_by_id(intake_id)
        if intake is None:
            raise NotFoundError(f"Intake {intake_id} not found")
        return intake
