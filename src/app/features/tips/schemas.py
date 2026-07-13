import uuid

from app.common.schema import CamelModel
from app.features.tips.models import Tip


class TipDto(CamelModel):
    id: str
    category: str
    tags: list[str]
    icon: str
    color: str
    title_en: str
    title_ar: str
    body_en: str
    body_ar: str

    @classmethod
    def from_model(cls, tip: Tip) -> "TipDto":
        return cls(
            id=str(tip.id),
            category=tip.category,
            tags=list(tip.tags),
            icon=tip.icon,
            color=tip.color,
            title_en=tip.title_en,
            title_ar=tip.title_ar,
            body_en=tip.body_en,
            body_ar=tip.body_ar,
        )


class SendTipRequest(CamelModel):
    patient_id: uuid.UUID


class SendTipResultDto(CamelModel):
    tip_id: str
    patient_id: str
    channel: str
    status: str
