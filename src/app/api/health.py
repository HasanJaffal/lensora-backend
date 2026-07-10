from fastapi import APIRouter

from app.common.envelope import Envelope, ok
from app.common.schema import CamelModel

router = APIRouter(tags=["health"])


class HealthDto(CamelModel):
    status: str


@router.get("/health")
async def health() -> Envelope[HealthDto]:
    return ok(HealthDto(status="ok"))
