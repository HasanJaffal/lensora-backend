from decimal import Decimal

from app.common.schema import CamelModel


class KpiDto(CamelModel):
    value: Decimal
    delta: str


class DashboardKpisDto(CamelModel):
    appointments_today: KpiDto
    orders_in_lab: KpiDto
    stock_alerts: KpiDto
    revenue_this_month: KpiDto


class SchedulePatientDto(CamelModel):
    id: str
    name: str
    avatar: str


class ScheduleEntryDto(CamelModel):
    time: str
    patient: SchedulePatientDto
    reason: str
    status: str


class ReadyForPickupDto(CamelModel):
    patient_id: str
    patient_name: str
    product: str
    total_due: Decimal | None


class LowStockAlertDto(CamelModel):
    id: str
    name: str
    sku: str
    qty: int  # maps to InventoryItem.quantity; `qty` is the stable frontend API contract
    threshold: int
    status: str


class GreetingDto(CamelModel):
    doctor_name_en: str
    doctor_name_ar: str
    appointments_today: int
    orders_in_lab: int
    stock_alerts: int


class DashboardSummaryDto(CamelModel):
    kpis: DashboardKpisDto
    schedule: list[ScheduleEntryDto]
    ready_for_pickup: list[ReadyForPickupDto]
    low_stock: list[LowStockAlertDto]
    greeting: GreetingDto
