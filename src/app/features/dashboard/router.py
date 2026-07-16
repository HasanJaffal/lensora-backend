from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.deps import CurrentUser, SessionDep
from app.common.envelope import Envelope, ok
from app.features.dashboard.schemas import DashboardSummaryDto
from app.features.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(session: SessionDep) -> DashboardService:
    return DashboardService(session)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get("/summary")
async def get_summary(
    current_user: CurrentUser, service: DashboardServiceDep
) -> Envelope[DashboardSummaryDto]:
    return ok(await service.get_summary(current_user))
