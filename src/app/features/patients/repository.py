import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.patients.models import LensConfig, Patient, PatientStatus


class PatientRepository(TenantScopedRepository):
    """Data access for patient records. No business rules live here."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    def _apply_filters(
        self,
        statement: Select[tuple[Patient]],
        *,
        status: PatientStatus | None,
        query: str | None,
    ) -> Select[tuple[Patient]]:
        if status is not None:
            statement = statement.where(Patient.status == status)
        if query:
            pattern = f"%{query}%"
            statement = statement.outerjoin(Patient.lens_config).where(
                or_(
                    Patient.name_en.ilike(pattern),
                    Patient.name_ar.ilike(pattern),
                    Patient.phone.ilike(pattern),
                    Patient.rx_number.ilike(pattern),
                    LensConfig.frame_sku.ilike(pattern),
                )
            )
        return statement

    async def list_page(
        self,
        *,
        status: PatientStatus | None,
        query: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Patient], int]:
        base = self._apply_filters(self.scoped_select(Patient), status=status, query=query)
        total = await self._session.scalar(
            select(func.count()).select_from(base.order_by(None).subquery())
        )
        page = await self._session.execute(
            base.options(selectinload(Patient.lens_config))
            .order_by(Patient.last_visit.desc(), Patient.name_en)
            .offset(offset)
            .limit(limit)
        )
        return list(page.scalars().unique().all()), total or 0

    async def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        result = await self._session.execute(
            self.scoped_select(Patient)
            .where(Patient.id == patient_id)
            .options(
                selectinload(Patient.notes),
                selectinload(Patient.visits),
                selectinload(Patient.lens_config),
            )
        )
        return result.scalar_one_or_none()

    def add(self, patient: Patient) -> None:
        self.add_scoped(patient)

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, patient: Patient) -> None:
        await self._session.refresh(patient, attribute_names=["notes", "visits", "lens_config"])
