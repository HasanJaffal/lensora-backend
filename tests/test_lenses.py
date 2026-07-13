from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.inventory.models import InventoryItem
from app.features.lenses.pricing import LineItem, price_order
from app.features.lenses.schemas import CreateOrderRequest
from app.features.lenses.service import OrderService


def _line(price: str) -> LineItem:
    return LineItem(label_en="x", label_ar="x", price=Decimal(price))


def test_price_order_sums_items_and_applies_deposit() -> None:
    priced = price_order(
        (_line("40"), _line("25"), _line("20"), _line("30"), _line("0"), _line("145")),
        deposit_percent=Decimal("0.40"),
    )

    assert priced.total == Decimal("260.00")
    assert priced.deposit == Decimal("104.00")
    assert priced.deposit_percent == Decimal("0.40")


def test_price_order_deposit_rounds_to_cents() -> None:
    priced = price_order((_line("99.99"),), deposit_percent=Decimal("0.40"))

    assert priced.total == Decimal("99.99")
    assert priced.deposit == Decimal("40.00")


async def _catalog_ids(client: AsyncClient) -> dict[str, dict[str, str]]:
    response = await client.get("/api/v1/lenses/catalog")
    assert response.status_code == 200
    data = response.json()["data"]
    return {
        group: {option["nameEn"]: option["id"] for option in data[group]}
        for group in ("types", "materials", "coatings", "tints")
    }


async def _frame(client: AsyncClient, *, in_stock: bool) -> dict:
    response = await client.get("/api/v1/inventory", params={"category": "frame"})
    frames = response.json()["data"]
    return next(f for f in frames if (f["qty"] > 0) == in_stock)


async def _patient_id(client: AsyncClient, name_en: str) -> str:
    response = await client.get("/api/v1/patients", params={"pageSize": 100})
    return next(p["id"] for p in response.json()["data"] if p["nameEn"] == name_en)


async def _valid_order_payload(client: AsyncClient, patient_id: str) -> dict:
    ids = await _catalog_ids(client)
    frame = await _frame(client, in_stock=True)
    return {
        "patientId": patient_id,
        "lensTypeId": ids["types"]["Single Vision"],
        "materialId": ids["materials"]["Thin 1.60"],
        "coatingIds": [ids["coatings"]["Anti-Reflective"], ids["coatings"]["Anti-Blue"]],
        "tintId": ids["tints"]["Clear"],
        "frameId": frame["id"],
    }, frame


async def test_catalog_returns_all_four_option_groups(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/lenses/catalog")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["types"]) == 4
    assert len(data["materials"]) == 4
    assert len(data["coatings"]) == 5
    assert len(data["tints"]) == 5
    single_vision = next(t for t in data["types"] if t["nameEn"] == "Single Vision")
    assert Decimal(str(single_vision["price"])) == Decimal("40.00")
    assert single_vision["nameAr"]


async def test_create_order_prices_and_sets_patient_to_lab(api_client: AsyncClient) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")
    payload, frame = await _valid_order_payload(api_client, patient_id)

    response = await api_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 200
    order = response.json()["data"]
    expected_total = Decimal("40") + Decimal("25") + Decimal("20") + Decimal("30") + (
        Decimal(str(frame["price"]))
    )
    assert Decimal(str(order["total"])) == expected_total
    assert Decimal(str(order["deposit"])) == (expected_total * Decimal("0.40")).quantize(
        Decimal("0.01")
    )
    assert len(order["items"]) == 6
    assert order["frame"]["sku"] == frame["sku"]

    patient = await api_client.get(f"/api/v1/patients/{patient_id}")
    assert patient.json()["data"]["status"] == "lab"


async def test_created_order_is_retrievable_by_id_and_by_patient(
    api_client: AsyncClient,
) -> None:
    patient_id = await _patient_id(api_client, "Hassan Zein")
    payload, _ = await _valid_order_payload(api_client, patient_id)
    created = await api_client.post("/api/v1/lenses/orders", json=payload)
    order_id = created.json()["data"]["id"]

    by_id = await api_client.get(f"/api/v1/lenses/orders/{order_id}")
    by_patient = await api_client.get(f"/api/v1/lenses/patients/{patient_id}/order")

    assert by_id.json()["data"]["id"] == order_id
    assert by_patient.json()["data"]["id"] == order_id


async def test_order_with_out_of_stock_frame_is_rejected(api_client: AsyncClient) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")
    payload, _ = await _valid_order_payload(api_client, patient_id)
    out_frame = await _frame(api_client, in_stock=False)
    payload["frameId"] = out_frame["id"]

    response = await api_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "inventory.outOfStock"


async def test_order_for_unknown_patient_returns_not_found(api_client: AsyncClient) -> None:
    payload, _ = await _valid_order_payload(
        api_client, "00000000-0000-0000-0000-000000000000"
    )

    response = await api_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_order_with_unknown_option_returns_validation_error(
    api_client: AsyncClient,
) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")
    payload, _ = await _valid_order_payload(api_client, patient_id)
    payload["materialId"] = "00000000-0000-0000-0000-000000000000"

    response = await api_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_patient_without_order_returns_not_found(api_client: AsyncClient) -> None:
    patient_id = await _patient_id(api_client, "Nour Saad")

    response = await api_client.get(f"/api/v1/lenses/patients/{patient_id}/order")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_stock_decrement_toggle_reduces_frame_quantity(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session:
        frame = await session.scalar(
            select(InventoryItem).where(InventoryItem.category == "frame", InventoryItem.qty > 0)
        )
        assert frame is not None
        starting_qty = frame.qty
        frame_id = frame.id
        request = await _build_service_order_request(session, frame_id)

    service = OrderService(session, db_sessionmaker, decrement_frame_stock=True)
    await service.create_order(request)

    async with db_sessionmaker() as session:
        refreshed = await session.get(InventoryItem, frame_id)
        assert refreshed is not None
        assert refreshed.qty == starting_qty - 1


async def _build_service_order_request(
    session: AsyncSession, frame_id: object
) -> CreateOrderRequest:
    from app.features.lenses.models import LensMaterial, LensTint, LensType
    from app.features.patients.models import Patient

    patient = await session.scalar(select(Patient).limit(1))
    lens_type = await session.scalar(select(LensType).limit(1))
    material = await session.scalar(select(LensMaterial).limit(1))
    tint = await session.scalar(select(LensTint).limit(1))
    assert patient and lens_type and material and tint
    return CreateOrderRequest(
        patient_id=patient.id,
        lens_type_id=lens_type.id,
        material_id=material.id,
        coating_ids=[],
        tint_id=tint.id,
        frame_id=frame_id,  # type: ignore[arg-type]
    )
