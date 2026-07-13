import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.intake.models import IntakeStatus, IntakeSubmission


class IntakeRepository:
    """Data access for intake submissions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, intake: IntakeSubmission) -> None:
        self._session.add(intake)

    async def get_by_id(self, intake_id: uuid.UUID) -> IntakeSubmission | None:
        return await self._session.get(IntakeSubmission, intake_id)

    async def list_submissions(
        self,
        *,
        patient_id: uuid.UUID | None = None,
        status: IntakeStatus | None = None,
    ) -> list[IntakeSubmission]:
        statement = select(IntakeSubmission).order_by(
            IntakeSubmission.created_at.desc()
        )
        if patient_id is not None:
            statement = statement.where(IntakeSubmission.patient_id == patient_id)
        if status is not None:
            statement = statement.where(IntakeSubmission.status == status)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, intake: IntakeSubmission) -> None:
        await self._session.refresh(intake)
