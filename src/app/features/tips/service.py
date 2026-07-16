import logging
import uuid

from app.common.exceptions import NotFoundError, PatientNotFoundError
from app.features.patients.repository import PatientRepository
from app.features.tips.matching import MAX_MATCHED_TIPS, select_matched_tips
from app.features.tips.models import TipCategory
from app.features.tips.repository import TipRepository
from app.features.tips.schemas import SendTipResultDto, TipDto

_SMS_CHANNEL = "sms"
_SEND_ACCEPTED = "accepted"

logger = logging.getLogger(__name__)


class TipService:
    """Business logic for the tips library: listing, tag matching, and send intent."""

    def __init__(self, tips: TipRepository, patients: PatientRepository) -> None:
        self._tips = tips
        self._patients = patients

    async def list_tips(self, *, category: TipCategory | None) -> list[TipDto]:
        records = await self._tips.list_tips(category=category)
        return [TipDto.from_model(record) for record in records]

    async def matched_tips(self, patient_id: uuid.UUID) -> list[TipDto]:
        patient = await self._patients.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")
        tips = await self._tips.list_tips()
        matched = select_matched_tips(tips, patient.tags, limit=MAX_MATCHED_TIPS)
        return [TipDto.from_model(tip) for tip in matched]

    async def send_tip(self, tip_id: uuid.UUID, patient_id: uuid.UUID) -> SendTipResultDto:
        tip = await self._tips.get_by_id(tip_id)
        if tip is None:
            raise NotFoundError(f"Tip {tip_id} not found")
        patient = await self._patients.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        # No SMS provider is integrated yet (BRD §7.2); record intent and acknowledge.
        logger.info("Tip %s queued for patient %s via %s", tip_id, patient_id, _SMS_CHANNEL)
        return SendTipResultDto(
            tip_id=str(tip_id),
            patient_id=str(patient_id),
            channel=_SMS_CHANNEL,
            status=_SEND_ACCEPTED,
        )
