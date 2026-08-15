from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.db.seeds import INVENTORY_ITEMS
from app.features.inventory.status import (
    StockStatus,
    derive_stock_status,
    quantity_ratio,
)


@pytest.mark.parametrize(
    ("qty", "threshold", "expected"),
    [
        (0, 2, StockStatus.OUT),
        (2, 2, StockStatus.LOW),
        (1, 3, StockStatus.LOW),
        (5, 2, StockStatus.IN_STOCK),
    ],
)
def test_derive_stock_status(qty: int, threshold: int, expected: StockStatus) -> None:
    assert derive_stock_status(qty, threshold) == expected


def test_quantity_ratio_bounds() -> None:
    assert quantity_ratio(0, 4) == 0.0
    assert quantity_ratio(4, 4) == 0.5
    assert quantity_ratio(100, 4) == 1.0


async def test_list_returns_all_items_with_derived_status(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory")

    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == len(INVENTORY_ITEMS)
    statuses = {item["status"] for item in items}
    assert statuses == {"inStock", "low", "out"}


async def test_stats_match_seed_data(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory/stats")

    assert response.status_code == 200
    stats = response.json()["data"]
    expected_low = sum(1 for i in INVENTORY_ITEMS if i.quantity <= i.threshold)
    expected_out = sum(1 for i in INVENTORY_ITEMS if i.quantity == 0)
    expected_value = sum((i.price * i.quantity for i in INVENTORY_ITEMS), start=Decimal("0"))

    assert stats["totalSkus"] == len(INVENTORY_ITEMS)
    assert stats["lowStockCount"] == expected_low
    assert stats["outOfStockCount"] == expected_out
    assert Decimal(str(stats["totalValue"])) == expected_value


async def test_category_filter_returns_only_that_category(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory", params={"category": "frame"})

    assert response.status_code == 200
    items = response.json()["data"]
    assert items
    assert all(item["category"] == "frame" for item in items)


async def test_low_stock_filter_returns_items_at_or_below_threshold(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/inventory", params={"lowStock": "true"})

    assert response.status_code == 200
    items = response.json()["data"]
    assert all(item["qty"] <= item["threshold"] for item in items)
    assert len(items) == sum(1 for i in INVENTORY_ITEMS if i.quantity <= i.threshold)


async def test_unknown_category_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory", params={"category": "widgets"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_frames_in_stock_excludes_out_of_stock(api_client: AsyncClient) -> None:
    response = await api_client.get(
        "/api/v1/inventory/frames", params={"use": "eyeglasses", "inStock": "true"}
    )

    assert response.status_code == 200
    frames = response.json()["data"]
    assert all(frame["category"] == "frame" for frame in frames)
    assert all(frame["qty"] > 0 for frame in frames)
    expected = sum(1 for i in INVENTORY_ITEMS if i.category == "frame" and i.quantity > 0)
    assert len(frames) == expected


async def test_frames_use_switches_catalog_to_sunglasses(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory/frames", params={"use": "sunglasses"})

    assert response.status_code == 200
    assert all(frame["category"] == "sun" for frame in response.json()["data"])


async def test_patch_updates_qty_and_recomputes_status(api_client: AsyncClient) -> None:
    listing = await api_client.get("/api/v1/inventory", params={"category": "frame"})
    item = next(i for i in listing.json()["data"] if i["qty"] > i["threshold"])

    response = await api_client.patch(f"/api/v1/inventory/{item['id']}", json={"qty": 0})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["qty"] == 0
    assert data["status"] == "out"


def _new_item_payload(sku: str = "TEST-SKU-001") -> dict[str, object]:
    return {
        "category": "frame",
        "name": "Test Frame",
        "brand": "Testwear",
        "spec": "52-18-140",
        "shape": "rectangular",
        "color": "black",
        "sku": sku,
        "qty": 6,
        "threshold": 2,
        "price": "129.00",
    }


async def test_create_adds_item_with_derived_status(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/inventory", json=_new_item_payload())

    assert response.status_code == 200
    item = response.json()["data"]
    assert item["sku"] == "TEST-SKU-001"
    assert item["qty"] == 6
    assert item["status"] == "inStock"

    listing = await api_client.get("/api/v1/inventory", params={"category": "frame"})
    assert any(i["sku"] == "TEST-SKU-001" for i in listing.json()["data"])


async def test_create_rejects_duplicate_sku_within_organization(api_client: AsyncClient) -> None:
    first = await api_client.post("/api/v1/inventory", json=_new_item_payload("DUPE-SKU"))
    assert first.status_code == 200

    response = await api_client.post("/api/v1/inventory", json=_new_item_payload("DUPE-SKU"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "inventory.skuTaken"


async def test_create_rejects_negative_quantity(api_client: AsyncClient) -> None:
    payload = _new_item_payload("NEG-SKU") | {"qty": -1}

    response = await api_client.post("/api/v1/inventory", json=payload)

    assert response.status_code == 422


async def test_delete_removes_item(api_client: AsyncClient) -> None:
    created = await api_client.post("/api/v1/inventory", json=_new_item_payload("GONE-SKU"))
    item_id = created.json()["data"]["id"]

    response = await api_client.delete(f"/api/v1/inventory/{item_id}")

    assert response.status_code == 200
    assert (await api_client.get(f"/api/v1/inventory/{item_id}")).status_code == 404


async def test_delete_unknown_item_returns_not_found(api_client: AsyncClient) -> None:
    response = await api_client.delete("/api/v1/inventory/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_get_unknown_item_returns_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/inventory/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_inventory_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/inventory")

    assert response.status_code == 401
