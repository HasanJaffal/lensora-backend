from datetime import date
from decimal import Decimal

from httpx import AsyncClient


async def _patients_by_name(client: AsyncClient) -> dict[str, dict]:
    response = await client.get("/api/v1/patients", params={"pageSize": 100})
    assert response.status_code == 200
    return {item["nameEn"]: item for item in response.json()["data"]}


async def test_list_returns_all_patients_with_pagination_meta(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/patients")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 4
    assert body["meta"]["pagination"]["total"] == 4


async def test_list_item_carries_rx_summary_and_computed_age(
    api_client: AsyncClient,
) -> None:
    patients = await _patients_by_name(api_client)
    layla = patients["Layla Haidar"]

    assert layla["nameAr"] == "ليلى حيدر"
    assert layla["age"] == date.today().year - 1991
    assert Decimal(str(layla["rxSummary"]["odSph"])) == Decimal("-2.25")


async def test_status_filter_returns_correct_subset(api_client: AsyncClient) -> None:
    lab = await api_client.get("/api/v1/patients", params={"status": "lab"})
    active = await api_client.get("/api/v1/patients", params={"status": "active"})
    every = await api_client.get("/api/v1/patients", params={"status": "all"})

    assert {p["nameEn"] for p in lab.json()["data"]} == {"Kamal Fakih"}
    assert len(active.json()["data"]) == 2
    assert len(every.json()["data"]) == 4


async def test_unknown_status_filter_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/patients", params={"status": "bogus"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_search_matches_name_phone_and_frame_sku(api_client: AsyncClient) -> None:
    by_name = await api_client.get("/api/v1/patients", params={"q": "Layla"})
    by_ar_name = await api_client.get("/api/v1/patients", params={"q": "كمال"})
    by_frame = await api_client.get("/api/v1/patients", params={"q": "FRM-GUC"})

    assert {p["nameEn"] for p in by_name.json()["data"]} == {"Layla Haidar"}
    assert {p["nameEn"] for p in by_ar_name.json()["data"]} == {"Kamal Fakih"}
    assert {p["nameEn"] for p in by_frame.json()["data"]} == {"Hassan Zein"}


async def test_get_full_record_matches_four_tab_needs(api_client: AsyncClient) -> None:
    patients = await _patients_by_name(api_client)
    patient_id = patients["Kamal Fakih"]["id"]

    response = await api_client.get(f"/api/v1/patients/{patient_id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["diagnosisAr"]
    assert Decimal(str(data["refraction"]["od"]["add"])) == Decimal("2.00")
    assert data["rxNumber"] == "card Nr. 00281"
    assert data["lensConfig"]["lensType"] == "Progressive / Varilux"
    assert len(data["history"]) == 1
    assert data["tags"] == ["presbyopia", "progressive"]


async def test_get_unknown_patient_returns_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get(
        "/api/v1/patients/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_history_endpoint_returns_visits_newest_first(
    api_client: AsyncClient,
) -> None:
    patients = await _patients_by_name(api_client)
    patient_id = patients["Layla Haidar"]["id"]

    response = await api_client.get(f"/api/v1/patients/{patient_id}/history")

    assert response.status_code == 200
    dates = [visit["date"] for visit in response.json()["data"]]
    assert dates == sorted(dates, reverse=True)


async def test_create_patient_persists_and_computes_age(api_client: AsyncClient) -> None:
    payload = {
        "nameEn": "Sara Khalil",
        "nameAr": "سارة خليل",
        "phone": "+961 70 555 000",
        "townEn": "Tyre",
        "townAr": "صور",
        "birthYear": 2000,
        "status": "active",
        "refraction": {
            "od": {"sph": "-1.50", "cyl": "-0.25", "axis": 90, "add": None},
            "os": {"sph": "-1.75", "cyl": None, "axis": None, "add": None},
        },
        "tags": ["myopia"],
        "notes": [{"en": "First visit", "ar": "الزيارة الأولى"}],
    }

    created = await api_client.post("/api/v1/patients", json=payload)

    assert created.status_code == 200
    data = created.json()["data"]
    assert data["age"] == date.today().year - 2000
    assert data["notes"][0]["ar"] == "الزيارة الأولى"

    fetched = await api_client.get(f"/api/v1/patients/{data['id']}")
    assert fetched.json()["data"]["nameEn"] == "Sara Khalil"


async def test_update_patient_changes_status_and_tags(api_client: AsyncClient) -> None:
    patients = await _patients_by_name(api_client)
    patient_id = patients["Nour Saad"]["id"]

    response = await api_client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"status": "active", "tags": ["child", "myopia", "screen"]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "active"
    assert data["tags"] == ["child", "myopia", "screen"]


async def test_patients_endpoint_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/patients")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.sessionExpired"
