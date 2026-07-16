from decimal import Decimal

from httpx import AsyncClient


async def _summary(client: AsyncClient) -> dict:
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    return response.json()["data"]


async def test_summary_returns_all_five_sections(api_client: AsyncClient) -> None:
    data = await _summary(api_client)

    assert set(data["kpis"]) == {
        "appointmentsToday",
        "ordersInLab",
        "stockAlerts",
        "revenueThisMonth",
    }
    assert "schedule" in data
    assert "readyForPickup" in data
    assert "lowStock" in data
    assert "greeting" in data


async def test_kpis_match_underlying_data(api_client: AsyncClient) -> None:
    data = await _summary(api_client)
    stats = (await api_client.get("/api/v1/inventory/stats")).json()["data"]

    assert int(Decimal(str(data["kpis"]["ordersInLab"]["value"]))) == 1
    assert int(Decimal(str(data["kpis"]["stockAlerts"]["value"]))) == stats["lowStockCount"]
    assert int(Decimal(str(data["kpis"]["appointmentsToday"]["value"]))) == len(data["schedule"])


async def test_schedule_is_time_ordered_with_patient_details(
    api_client: AsyncClient,
) -> None:
    data = await _summary(api_client)
    schedule = data["schedule"]

    assert schedule
    times = [entry["time"] for entry in schedule]
    assert times == sorted(times)
    first = schedule[0]
    assert first["patient"]["id"]
    assert first["patient"]["avatar"]
    assert first["reason"] in {"lensFitting", "pickup", "followUp"}


async def test_ready_for_pickup_lists_ready_patients(api_client: AsyncClient) -> None:
    data = await _summary(api_client)

    names = {entry["patientName"] for entry in data["readyForPickup"]}
    assert "Nour Saad" in names
    nour = next(e for e in data["readyForPickup"] if e["patientName"] == "Nour Saad")
    assert nour["product"] == "Round Slim"


async def test_low_stock_alert_matches_inventory_and_is_capped(
    api_client: AsyncClient,
) -> None:
    data = await _summary(api_client)

    assert len(data["lowStock"]) <= 5
    assert all(item["qty"] <= item["threshold"] for item in data["lowStock"])


async def test_greeting_carries_bilingual_doctor_and_counts(
    api_client: AsyncClient,
) -> None:
    data = await _summary(api_client)
    greeting = data["greeting"]

    assert greeting["doctorNameEn"]
    assert greeting["doctorNameAr"]
    assert greeting["ordersInLab"] == 1


async def _catalog_and_frame(client: AsyncClient) -> dict:
    catalog = (await client.get("/api/v1/lenses/catalog")).json()["data"]
    frames = (await client.get("/api/v1/inventory", params={"category": "frame"})).json()["data"]
    frame = next(f for f in frames if f["qty"] > 0)
    patients = (await client.get("/api/v1/patients", params={"pageSize": 100})).json()["data"]
    patient_id = next(p["id"] for p in patients if p["nameEn"] == "Layla Haidar")
    return {
        "patientId": patient_id,
        "lensTypeId": catalog["types"][0]["id"],
        "materialId": catalog["materials"][0]["id"],
        "coatingIds": [],
        "tintId": catalog["tints"][0]["id"],
        "frameId": frame["id"],
    }


async def test_new_order_updates_lab_count_and_revenue(api_client: AsyncClient) -> None:
    before = await _summary(api_client)
    lab_before = int(Decimal(str(before["kpis"]["ordersInLab"]["value"])))

    payload = await _catalog_and_frame(api_client)
    created = await api_client.post("/api/v1/lenses/orders", json=payload)
    total = Decimal(str(created.json()["data"]["total"]))

    after = await _summary(api_client)
    assert int(Decimal(str(after["kpis"]["ordersInLab"]["value"]))) == lab_before + 1
    assert Decimal(str(after["kpis"]["revenueThisMonth"]["value"])) == total


async def test_dashboard_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401
