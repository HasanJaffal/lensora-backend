"""Mandatory cross-tenant isolation tests (Phase B5).

With Org A's authenticated client, every read/update/delete of an Org B resource must come
back as 404 `resource.notFound` (or the resource-specific not-found code) — never a leak of
Org B's data and never a distinguishable "exists but forbidden" response.
"""

from httpx import AsyncClient


async def _patient_id(client: AsyncClient, name_en: str) -> str:
    response = await client.get("/api/v1/patients", params={"pageSize": 100})
    return next(p["id"] for p in response.json()["data"] if p["nameEn"] == name_en)


async def _first_frame_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/inventory", params={"category": "frame"})
    frames = response.json()["data"]
    return next(f for f in frames if f["qty"] > 0)["id"]


async def _catalog_ids(client: AsyncClient) -> dict[str, dict[str, str]]:
    response = await client.get("/api/v1/lenses/catalog")
    data = response.json()["data"]
    return {
        group: {option["nameEn"]: option["id"] for option in data[group]}
        for group in ("types", "materials", "coatings", "tints")
    }


async def _create_order_for_org_b(org_b_client: AsyncClient) -> dict:
    patient_id = await _patient_id(org_b_client, "Layla Haidar")
    ids = await _catalog_ids(org_b_client)
    frame_id = await _first_frame_id(org_b_client)
    payload = {
        "patientId": patient_id,
        "lensTypeId": ids["types"]["Single Vision"],
        "materialId": ids["materials"]["Thin 1.60"],
        "coatingIds": [ids["coatings"]["Anti-Reflective"]],
        "tintId": ids["tints"]["Clear"],
        "frameId": frame_id,
    }
    response = await org_b_client.post("/api/v1/lenses/orders", json=payload)
    assert response.status_code == 200
    return response.json()["data"]


async def test_org_a_cannot_read_org_bs_patient(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_patient_id = await _patient_id(org_b_client, "Layla Haidar")

    response = await org_a_client.get(f"/api/v1/patients/{org_b_patient_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_org_a_cannot_update_org_bs_patient(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_patient_id = await _patient_id(org_b_client, "Layla Haidar")
    before = (await org_b_client.get(f"/api/v1/patients/{org_b_patient_id}")).json()["data"]

    response = await org_a_client.patch(
        f"/api/v1/patients/{org_b_patient_id}",
        json={"townEn": "Tampered-By-Org-A"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"

    after = (await org_b_client.get(f"/api/v1/patients/{org_b_patient_id}")).json()["data"]
    assert after["townEn"] == before["townEn"]


async def test_org_a_cannot_read_org_bs_patient_history(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_patient_id = await _patient_id(org_b_client, "Layla Haidar")

    response = await org_a_client.get(f"/api/v1/patients/{org_b_patient_id}/history")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_org_a_patient_list_excludes_org_b_patients(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_names = {
        patient["nameEn"]
        for patient in (
            await org_b_client.get("/api/v1/patients", params={"pageSize": 100})
        ).json()["data"]
    }
    org_a_names = {
        patient["nameEn"]
        for patient in (
            await org_a_client.get("/api/v1/patients", params={"pageSize": 100})
        ).json()["data"]
    }

    assert org_a_names == org_b_names
    org_a_ids = {
        patient["id"]
        for patient in (
            await org_a_client.get("/api/v1/patients", params={"pageSize": 100})
        ).json()["data"]
    }
    org_b_ids = {
        patient["id"]
        for patient in (
            await org_b_client.get("/api/v1/patients", params={"pageSize": 100})
        ).json()["data"]
    }
    assert org_a_ids.isdisjoint(org_b_ids)


async def test_org_a_cannot_read_org_bs_inventory_item(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_item_id = await _first_frame_id(org_b_client)

    response = await org_a_client.get(f"/api/v1/inventory/{org_b_item_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_org_a_cannot_update_org_bs_inventory_item(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_item_id = await _first_frame_id(org_b_client)

    response = await org_a_client.patch(f"/api/v1/inventory/{org_b_item_id}", json={"qty": 0})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"

    unaffected = await org_b_client.get(f"/api/v1/inventory/{org_b_item_id}")
    assert unaffected.json()["data"]["qty"] != 0


async def test_org_a_cannot_delete_org_bs_inventory_item(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_item_id = await _first_frame_id(org_b_client)

    response = await org_a_client.delete(f"/api/v1/inventory/{org_b_item_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"

    unaffected = await org_b_client.get(f"/api/v1/inventory/{org_b_item_id}")
    assert unaffected.status_code == 200


async def test_both_orgs_can_use_the_same_inventory_sku(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    payload = {
        "category": "frame",
        "name": "Shared SKU Frame",
        "brand": "Testwear",
        "spec": "52-18-140",
        "sku": "SHARED-SKU",
        "qty": 4,
        "threshold": 1,
        "price": "99.00",
    }

    assert (await org_a_client.post("/api/v1/inventory", json=payload)).status_code == 200
    assert (await org_b_client.post("/api/v1/inventory", json=payload)).status_code == 200


async def test_org_a_cannot_read_org_bs_order(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_order = await _create_order_for_org_b(org_b_client)

    response = await org_a_client.get(f"/api/v1/lenses/orders/{org_b_order['id']}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_org_a_cannot_read_org_bs_patient_order(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    await _create_order_for_org_b(org_b_client)
    org_b_patient_id = await _patient_id(org_b_client, "Layla Haidar")

    response = await org_a_client.get(f"/api/v1/lenses/patients/{org_b_patient_id}/order")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_org_a_cannot_order_with_org_bs_catalog_ids(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_a_patient_id = await _patient_id(org_a_client, "Layla Haidar")
    org_b_ids = await _catalog_ids(org_b_client)
    org_a_frame_id = await _first_frame_id(org_a_client)

    payload = {
        "patientId": org_a_patient_id,
        "lensTypeId": org_b_ids["types"]["Single Vision"],
        "materialId": org_b_ids["materials"]["Thin 1.60"],
        "coatingIds": [],
        "tintId": org_b_ids["tints"]["Clear"],
        "frameId": org_a_frame_id,
    }

    response = await org_a_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_org_a_cannot_order_with_org_bs_frame(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_a_patient_id = await _patient_id(org_a_client, "Layla Haidar")
    org_a_ids = await _catalog_ids(org_a_client)
    org_b_frame_id = await _first_frame_id(org_b_client)

    payload = {
        "patientId": org_a_patient_id,
        "lensTypeId": org_a_ids["types"]["Single Vision"],
        "materialId": org_a_ids["materials"]["Thin 1.60"],
        "coatingIds": [],
        "tintId": org_a_ids["tints"]["Clear"],
        "frameId": org_b_frame_id,
    }

    response = await org_a_client.post("/api/v1/lenses/orders", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_org_a_cannot_send_org_bs_tip(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_b_tip_id = (await org_b_client.get("/api/v1/tips")).json()["data"][0]["id"]
    org_a_patient_id = await _patient_id(org_a_client, "Layla Haidar")

    response = await org_a_client.post(
        f"/api/v1/tips/{org_b_tip_id}/send", json={"patientId": org_a_patient_id}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_org_a_tip_list_excludes_org_bs_tips(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_a_ids = {tip["id"] for tip in (await org_a_client.get("/api/v1/tips")).json()["data"]}
    org_b_ids = {tip["id"] for tip in (await org_b_client.get("/api/v1/tips")).json()["data"]}

    assert org_a_ids.isdisjoint(org_b_ids)


async def test_org_a_cannot_read_org_bs_intake(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    created = await org_b_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Org B Patient"}},
    )
    intake_id = created.json()["data"]["id"]

    response = await org_a_client.get(f"/api/v1/intake/{intake_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_org_a_cannot_update_org_bs_intake(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    created = await org_b_client.post(
        "/api/v1/intake",
        json={"status": "draft", "individualInfo": {"name": "Org B Patient"}},
    )
    intake_id = created.json()["data"]["id"]

    response = await org_a_client.patch(f"/api/v1/intake/{intake_id}", json={"status": "draft"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_org_a_and_org_b_dashboards_are_independent(
    org_a_client: AsyncClient, org_b_client: AsyncClient
) -> None:
    org_a_summary = (await org_a_client.get("/api/v1/dashboard/summary")).json()["data"]
    org_b_summary = (await org_b_client.get("/api/v1/dashboard/summary")).json()["data"]

    org_a_patient_ids = {entry["patient"]["id"] for entry in org_a_summary["schedule"]}
    org_b_patient_ids = {entry["patient"]["id"] for entry in org_b_summary["schedule"]}
    assert org_a_patient_ids.isdisjoint(org_b_patient_ids)
