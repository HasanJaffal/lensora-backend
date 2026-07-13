import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, require_auth
from app.common.envelope import Envelope, Meta, ok
from app.common.exceptions import ValidationError
from app.common.pagination import PageParams
from app.features.patients.models import PatientStatus
from app.features.patients.repository import PatientRepository
from app.features.patients.schemas import (
    PatientCreateRequest,
    PatientDto,
    PatientListItemDto,
    PatientUpdateRequest,
    VisitHistoryDto,
)
from app.features.patients.service import PatientService

router = APIRouter(
    prefix="/patients", tags=["patients"], dependencies=[Depends(require_auth)]
)


def get_patient_service(session: SessionDep) -> PatientService:
    return PatientService(PatientRepository(session))


PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]

_ALL_STATUSES = "all"


def _parse_status(status: str | None) -> PatientStatus | None:
    if status is None or status == _ALL_STATUSES:
        return None
    try:
        return PatientStatus(status)
    except ValueError as exc:
        allowed = ", ".join((_ALL_STATUSES, *(member.value for member in PatientStatus)))
        raise ValidationError(
            f"Unknown status filter '{status}'; expected one of: {allowed}"
        ) from exc


@router.get("")
async def list_patients(
    service: PatientServiceDep,
    page_params: Annotated[PageParams, Depends()],
    status: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> Envelope[list[PatientListItemDto]]:
    items, pagination = await service.list_patients(
        status=_parse_status(status),
        query=q,
        page=page_params.page,
        page_size=page_params.page_size,
        offset=page_params.offset,
    )
    return ok(items, meta=Meta(pagination=pagination))


@router.post("")
async def create_patient(
    body: PatientCreateRequest, service: PatientServiceDep
) -> Envelope[PatientDto]:
    return ok(await service.create_patient(body))


@router.get("/{patient_id}")
async def get_patient(
    patient_id: uuid.UUID, service: PatientServiceDep
) -> Envelope[PatientDto]:
    return ok(await service.get_patient(patient_id))


@router.patch("/{patient_id}")
async def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdateRequest,
    service: PatientServiceDep,
) -> Envelope[PatientDto]:
    return ok(await service.update_patient(patient_id, body))


@router.get("/{patient_id}/history")
async def get_patient_history(
    patient_id: uuid.UUID, service: PatientServiceDep
) -> Envelope[list[VisitHistoryDto]]:
    return ok(await service.get_history(patient_id))
