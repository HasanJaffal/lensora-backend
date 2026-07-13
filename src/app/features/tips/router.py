import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, require_auth
from app.common.envelope import Envelope, ok
from app.common.exceptions import ValidationError
from app.features.patients.repository import PatientRepository
from app.features.tips.models import TipCategory
from app.features.tips.repository import TipRepository
from app.features.tips.schemas import SendTipRequest, SendTipResultDto, TipDto
from app.features.tips.service import TipService

router = APIRouter(prefix="/tips", tags=["tips"], dependencies=[Depends(require_auth)])


def get_tip_service(session: SessionDep) -> TipService:
    return TipService(TipRepository(session), PatientRepository(session))


TipServiceDep = Annotated[TipService, Depends(get_tip_service)]


def _parse_category(category: str | None) -> TipCategory | None:
    if category is None:
        return None
    try:
        return TipCategory(category)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in TipCategory)
        raise ValidationError(
            f"Unknown category '{category}'; expected one of: {allowed}"
        ) from exc


@router.get("")
async def list_tips(
    service: TipServiceDep,
    category: Annotated[str | None, Query()] = None,
) -> Envelope[list[TipDto]]:
    return ok(await service.list_tips(category=_parse_category(category)))


@router.get("/matched")
async def matched_tips(
    service: TipServiceDep,
    patient_id: Annotated[uuid.UUID, Query(alias="patientId")],
) -> Envelope[list[TipDto]]:
    return ok(await service.matched_tips(patient_id))


@router.post("/{tip_id}/send")
async def send_tip(
    tip_id: uuid.UUID, body: SendTipRequest, service: TipServiceDep
) -> Envelope[SendTipResultDto]:
    return ok(await service.send_tip(tip_id, body.patient_id))
