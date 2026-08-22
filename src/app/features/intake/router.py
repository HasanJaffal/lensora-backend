import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, TenantContextDep, require_auth
from app.common.envelope import Envelope, ok
from app.common.exceptions import ValidationError
from app.features.intake.models import IntakeStatus
from app.features.intake.repository import IntakeRepository
from app.features.intake.schemas import (
    IntakeCreateRequest,
    IntakeDto,
    IntakeListItemDto,
    IntakeUpdateRequest,
)
from app.features.intake.service import IntakeService
from app.features.patients.repository import PatientRepository

router = APIRouter(prefix="/intake", tags=["intake"], dependencies=[Depends(require_auth)])


def get_intake_service(session: SessionDep, tenant_context: TenantContextDep) -> IntakeService:
    return IntakeService(
        IntakeRepository(session, tenant_context),
        PatientRepository(session, tenant_context),
    )


IntakeServiceDep = Annotated[IntakeService, Depends(get_intake_service)]


def _parse_status(status: str | None) -> IntakeStatus | None:
    if status is None:
        return None
    try:
        return IntakeStatus(status)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in IntakeStatus)
        raise ValidationError(f"Unknown status '{status}'; expected one of: {allowed}") from exc


@router.get("")
async def list_intakes(
    service: IntakeServiceDep,
    patient_id: Annotated[uuid.UUID | None, Query(alias="patientId")] = None,
    status: Annotated[str | None, Query()] = None,
) -> Envelope[list[IntakeListItemDto]]:
    return ok(await service.list_intakes(patient_id=patient_id, status=_parse_status(status)))


@router.post("")
async def create_intake(
    body: IntakeCreateRequest, service: IntakeServiceDep
) -> Envelope[IntakeDto]:
    return ok(await service.create_intake(body))


@router.get("/{intake_id}")
async def get_intake(intake_id: uuid.UUID, service: IntakeServiceDep) -> Envelope[IntakeDto]:
    return ok(await service.get_intake(intake_id))


@router.patch("/{intake_id}")
async def update_intake(
    intake_id: uuid.UUID,
    body: IntakeUpdateRequest,
    service: IntakeServiceDep,
) -> Envelope[IntakeDto]:
    return ok(await service.update_intake(intake_id, body))
