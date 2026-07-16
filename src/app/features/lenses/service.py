import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.envelope import ErrorDetail
from app.common.exceptions import (
    NotFoundError,
    OutOfStockError,
    PatientNotFoundError,
    ValidationError,
)
from app.common.tenant_context import TenantContext
from app.db.unit_of_work import UnitOfWork
from app.features.inventory.models import InventoryItem
from app.features.inventory.repository import InventoryRepository
from app.features.lenses.models import (
    LensCoating,
    LensMaterial,
    LensTint,
    LensType,
    Order,
    OrderItem,
)
from app.features.lenses.pricing import LineItem, PricedOrder, price_order
from app.features.lenses.repository import LensCatalogRepository, OrderRepository
from app.features.lenses.schemas import (
    CreateOrderRequest,
    LensCatalogDto,
    LensOptionDto,
    OrderDto,
)
from app.features.organizations.repository import OrganizationRepository
from app.features.patients.models import PatientStatus
from app.features.patients.repository import PatientRepository

DECREMENT_FRAME_STOCK_ON_ORDER = False


def _unknown_reference(field: str) -> ValidationError:
    return ValidationError(
        f"Unknown {field}",
        details=[ErrorDetail(field=field, message=f"Unknown {field}")],
    )


class LensCatalogService:
    """Read-only access to the four lens option catalogs (FR-LENS-2)."""

    def __init__(self, catalog: LensCatalogRepository) -> None:
        self._catalog = catalog

    async def get_catalog(self) -> LensCatalogDto:
        return LensCatalogDto(
            types=[LensOptionDto.from_model(o) for o in await self._catalog.list_types()],
            materials=[LensOptionDto.from_model(o) for o in await self._catalog.list_materials()],
            coatings=[LensOptionDto.from_model(o) for o in await self._catalog.list_coatings()],
            tints=[LensOptionDto.from_model(o) for o in await self._catalog.list_tints()],
        )


class OrderService:
    """Lens order creation (transactional, server-priced) and retrieval per FR-LENS."""

    def __init__(
        self,
        session: AsyncSession,
        sessionmaker: async_sessionmaker[AsyncSession],
        tenant_context: TenantContext,
        *,
        decrement_frame_stock: bool = DECREMENT_FRAME_STOCK_ON_ORDER,
    ) -> None:
        self._session = session
        self._sessionmaker = sessionmaker
        self._tenant_context = tenant_context
        self._decrement_frame_stock = decrement_frame_stock

    async def create_order(self, request: CreateOrderRequest) -> OrderDto:
        async with UnitOfWork(self._sessionmaker) as uow:
            patients = PatientRepository(uow.session, self._tenant_context)
            inventory = InventoryRepository(uow.session, self._tenant_context)
            catalog = LensCatalogRepository(uow.session, self._tenant_context)
            orders = OrderRepository(uow.session, self._tenant_context)
            organizations = OrganizationRepository(uow.session)

            patient = await patients.get_by_id(request.patient_id)
            if patient is None:
                raise PatientNotFoundError(f"Patient {request.patient_id} not found")

            lens_type = await catalog.get_type(request.lens_type_id)
            if lens_type is None:
                raise _unknown_reference("lensTypeId")
            material = await catalog.get_material(request.material_id)
            if material is None:
                raise _unknown_reference("materialId")
            tint = await catalog.get_tint(request.tint_id)
            if tint is None:
                raise _unknown_reference("tintId")
            coatings = await catalog.get_coatings(request.coating_ids)
            if len(coatings) != len(set(request.coating_ids)):
                raise _unknown_reference("coatingIds")

            frame = await inventory.get_by_id(request.frame_id)
            if frame is None:
                raise _unknown_reference("frameId")
            if frame.quantity <= 0:
                raise OutOfStockError(f"Frame {frame.sku} is out of stock")

            organization = await organizations.get_by_id(self._tenant_context.organization_id)
            assert organization is not None

            priced = _price(
                lens_type, material, coatings, tint, frame, organization.deposit_percent
            )
            order = _build_order(
                request.patient_id, priced, frame, self._tenant_context.organization_id
            )
            orders.add(order)

            patient.status = PatientStatus.LAB.value
            if self._decrement_frame_stock:
                frame.quantity -= 1

            await uow.session.flush()
            await uow.session.refresh(order, ["items", "created_at"])
            return OrderDto.from_model(order)

    async def get_order(self, order_id: uuid.UUID) -> OrderDto:
        order = await OrderRepository(self._session, self._tenant_context).get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        return OrderDto.from_model(order)

    async def get_current_order_for_patient(self, patient_id: uuid.UUID) -> OrderDto:
        patient = await PatientRepository(self._session, self._tenant_context).get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")
        order = await OrderRepository(self._session, self._tenant_context).get_latest_for_patient(
            patient_id
        )
        if order is None:
            raise NotFoundError(f"Patient {patient_id} has no lens order")
        return OrderDto.from_model(order)


def _price(
    lens_type: LensType,
    material: LensMaterial,
    coatings: list[LensCoating],
    tint: LensTint,
    frame: InventoryItem,
    deposit_percent: Decimal,
) -> PricedOrder:
    items: list[LineItem] = [
        LineItem(lens_type.name_en, lens_type.name_ar, lens_type.price),
        LineItem(material.name_en, material.name_ar, material.price),
    ]
    items.extend(LineItem(coating.name_en, coating.name_ar, coating.price) for coating in coatings)
    items.append(LineItem(tint.name_en, tint.name_ar, tint.price))
    items.append(LineItem(frame.name, frame.name, frame.price))
    return price_order(tuple(items), deposit_percent=deposit_percent)


def _build_order(
    patient_id: uuid.UUID,
    priced: PricedOrder,
    frame: InventoryItem,
    organization_id: uuid.UUID,
) -> Order:
    return Order(
        organization_id=organization_id,
        patient_id=patient_id,
        total=priced.total,
        deposit=priced.deposit,
        deposit_percent=priced.deposit_percent,
        frame_sku=frame.sku,
        frame_name=frame.name,
        items=[
            OrderItem(
                organization_id=organization_id,
                position=index,
                label_en=item.label_en,
                label_ar=item.label_ar,
                price=item.price,
            )
            for index, item in enumerate(priced.items)
        ],
    )
