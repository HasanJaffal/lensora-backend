from httpx import AsyncClient

from app.features.tips.matching import select_matched_tips
from app.features.tips.models import Tip


def _tip(title: str, tags: list[str]) -> Tip:
    return Tip(
        category="screen",
        tags=tags,
        icon="i",
        color="c",
        title_en=title,
        title_ar=title,
        body_en="b",
        body_ar="b",
    )


def test_select_matched_ranks_by_overlap_and_caps_limit() -> None:
    tips = [
        _tip("none", ["sun"]),
        _tip("one", ["screen"]),
        _tip("three", ["screen", "myopia", "astigmatism"]),
        _tip("two", ["myopia", "astigmatism"]),
    ]

    matched = select_matched_tips(tips, ["screen", "myopia", "astigmatism"], limit=4)

    assert [tip.title_en for tip in matched] == ["three", "two", "one"]


def test_select_matched_excludes_non_overlapping_and_respects_limit() -> None:
    tips = [_tip(str(i), ["screen"]) for i in range(6)]

    matched = select_matched_tips(tips, ["screen"], limit=4)

    assert len(matched) == 4


async def test_list_returns_all_tips(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/tips")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 10


async def test_category_filter_returns_only_that_category(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/tips", params={"category": "screen"})

    assert response.status_code == 200
    tips = response.json()["data"]
    assert tips
    assert all(tip["category"] == "screen" for tip in tips)


async def test_unknown_category_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/tips", params={"category": "nope"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def _patient_id(client: AsyncClient, name_en: str) -> str:
    response = await client.get("/api/v1/patients", params={"pageSize": 100})
    return next(p["id"] for p in response.json()["data"] if p["nameEn"] == name_en)


async def test_matched_returns_at_most_four_intersecting_tips(
    api_client: AsyncClient,
) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")

    response = await api_client.get("/api/v1/tips/matched", params={"patientId": patient_id})

    assert response.status_code == 200
    tips = response.json()["data"]
    assert 0 < len(tips) <= 4
    layla_tags = {"myopia", "astigmatism", "screen"}
    assert all(set(tip["tags"]) & layla_tags for tip in tips)
    assert any(tip["titleEn"] == "Follow the 20-20-20 rule" for tip in tips)


async def test_matched_for_unknown_patient_returns_not_found(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/tips/matched",
        params={"patientId": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_send_tip_returns_deterministic_ack(api_client: AsyncClient) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")
    tip = (await api_client.get("/api/v1/tips")).json()["data"][0]

    response = await api_client.post(
        f"/api/v1/tips/{tip['id']}/send", json={"patientId": patient_id}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "accepted"
    assert data["channel"] == "sms"
    assert data["tipId"] == tip["id"]


async def test_send_unknown_tip_returns_not_found(api_client: AsyncClient) -> None:
    patient_id = await _patient_id(api_client, "Layla Haidar")

    response = await api_client.post(
        "/api/v1/tips/00000000-0000-0000-0000-000000000000/send",
        json={"patientId": patient_id},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_tips_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tips")

    assert response.status_code == 401
