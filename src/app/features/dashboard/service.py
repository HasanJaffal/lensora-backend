from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.features.dashboard.schemas import (
    DashboardKpisDto,
    DashboardSummaryDto,
    GreetingDto,
    KpiDto,
    LowStockAlertDto,
    ReadyForPickupDto,
    ScheduleEntryDto,
    SchedulePatientDto,
)
from app.features.inventory.models import InventoryItem
from app.features.inventory.repository import InventoryRepository
from app.features.inventory.status import derive_stock_status
from app.features.lenses.repository import OrderRepository
from app.features.patients.models import Patient, PatientStatus
from app.features.patients.repository import PatientRepository

_MAX_PATIENTS = 200
_MAX_SCHEDULE = 6
_MAX_LOW_STOCK = 5
_SCHEDULE_START_HOUR = 9
_SLOT_MINUTES = 30

_REASON_BY_STATUS: dict[str, str] = {
    PatientStatus.LAB.value: "lensFitting",
    PatientStatus.READY.value: "pickup",
    PatientStatus.ACTIVE.value: "followUp",
}


class DashboardService:
    """Read-only aggregation for the dashboard, composing the other features (FR-DASH)."""

    def __init__(self, session: AsyncSession) -> None:
        self._patients = PatientRepository(session)
        self._inventory = InventoryRepository(session)
        self._orders = OrderRepository(session)

    async def get_summary(self, doctor: User) -> DashboardSummaryDto:
        patients, _ = await self._patients.list_page(
            status=None, query=None, offset=0, limit=_MAX_PATIENTS
        )
        inventory = await self._inventory.list_all()
        low_stock = [item for item in inventory if item.qty <= item.threshold]
        sku_to_name = {item.sku: item.name for item in inventory}

        lab_count = _count(patients, PatientStatus.LAB)
        active_count = _count(patients, PatientStatus.ACTIVE)
        out_count = sum(1 for item in low_stock if item.qty <= 0)
        revenue = await self._orders.total_revenue_since(_start_of_month())

        schedule = _build_schedule(patients)
        ready = await self._build_ready_for_pickup(patients, sku_to_name)

        return DashboardSummaryDto(
            kpis=DashboardKpisDto(
                appointments_today=KpiDto(
                    value=Decimal(len(schedule)), delta=f"+{active_count}"
                ),
                orders_in_lab=KpiDto(value=Decimal(lab_count), delta=f"+{lab_count}"),
                stock_alerts=KpiDto(value=Decimal(len(low_stock)), delta=f"+{out_count}"),
                revenue_this_month=KpiDto(value=revenue, delta=""),
            ),
            schedule=schedule,
            ready_for_pickup=ready,
            low_stock=_build_low_stock(low_stock),
            greeting=GreetingDto(
                doctor_name_en=doctor.display_name_en,
                doctor_name_ar=doctor.display_name_ar,
                appointments_today=len(schedule),
                orders_in_lab=lab_count,
                stock_alerts=len(low_stock),
            ),
        )

    async def _build_ready_for_pickup(
        self, patients: list[Patient], sku_to_name: dict[str, str]
    ) -> list[ReadyForPickupDto]:
        ready: list[ReadyForPickupDto] = []
        for patient in patients:
            if patient.status != PatientStatus.READY:
                continue
            order = await self._orders.get_latest_for_patient(patient.id)
            ready.append(
                ReadyForPickupDto(
                    patient_id=str(patient.id),
                    patient_name=patient.name_en,
                    product=_product_label(patient, sku_to_name),
                    total_due=order.total if order is not None else None,
                )
            )
        return ready


def _count(patients: list[Patient], status: PatientStatus) -> int:
    return sum(1 for patient in patients if patient.status == status)


def _start_of_month() -> datetime:
    today = date.today()
    return datetime(today.year, today.month, 1, tzinfo=UTC)


def _build_schedule(patients: list[Patient]) -> list[ScheduleEntryDto]:
    ordered = sorted(patients, key=lambda patient: patient.name_en)[:_MAX_SCHEDULE]
    return [
        ScheduleEntryDto(
            time=_slot_time(index),
            patient=SchedulePatientDto(
                id=str(patient.id),
                name=patient.name_en,
                avatar=_initials(patient.name_en),
            ),
            reason=_REASON_BY_STATUS.get(patient.status, "followUp"),
            status=patient.status,
        )
        for index, patient in enumerate(ordered)
    ]


def _build_low_stock(items: list[InventoryItem]) -> list[LowStockAlertDto]:
    most_critical = sorted(items, key=lambda item: (item.qty, item.qty / (item.threshold or 1)))
    return [
        LowStockAlertDto(
            id=str(item.id),
            name=item.name,
            sku=item.sku,
            qty=item.qty,
            threshold=item.threshold,
            status=derive_stock_status(item.qty, item.threshold),
        )
        for item in most_critical[:_MAX_LOW_STOCK]
    ]


def _slot_time(index: int) -> str:
    minutes = index * _SLOT_MINUTES
    hour = _SCHEDULE_START_HOUR + minutes // 60
    return f"{hour:02d}:{minutes % 60:02d}"


def _initials(name: str) -> str:
    parts = [word for word in name.split() if word]
    return "".join(word[0].upper() for word in parts[:2]) or "?"


def _product_label(patient: Patient, sku_to_name: dict[str, str]) -> str:
    config = patient.lens_config
    if config is not None and config.frame_sku in sku_to_name:
        return sku_to_name[config.frame_sku]
    if config is not None and config.lens_type:
        return config.lens_type
    return "—"
