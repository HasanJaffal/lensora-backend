from httpx import AsyncClient

from app.features.ai.context import (
    AssistantContext,
    FrameSummary,
    PatientSummary,
    StockSummary,
    StylingContext,
)
from app.features.ai.provider import FallbackProvider
from app.features.ai.schemas import Locale, ProductNeed


def _context() -> AssistantContext:
    return AssistantContext(
        patients=[
            PatientSummary("Layla", "Tyre", 34, "lab", "Myopia", "-2.25", "-2.50"),
            PatientSummary("Nour", "Saida", 11, "ready", "Myopia", "-1.00", "-1.25"),
        ],
        low_stock=[
            StockSummary("Photochromic 1.60", "LNS-PHOTO-160", 0, "out"),
            StockSummary("Toric Daily 30pk", "CON-DAI-TOR-30", 4, "low"),
        ],
    )


async def test_fallback_chat_is_deterministic_and_within_word_limit() -> None:
    provider = FallbackProvider()

    content = await provider.chat([], _context(), Locale.EN)

    assert "2 item" in content
    assert "1 patient" in content
    assert len(content.split()) <= 80


async def test_fallback_styling_advice_returns_two_to_three_tips() -> None:
    provider = FallbackProvider()
    context = StylingContext(
        frame=FrameSummary("Wayfarer", "Ray-Ban", "wayfarer", "Black"),
        need="eyeglasses",
        diagnosis="Myopia",
    )

    tips = await provider.styling_advice(context, Locale.EN)

    assert 2 <= len(tips) <= 3


async def test_chat_returns_fallback_response(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "Which items are low?"}], "locale": "en"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usedFallback"] is True
    assert data["message"]["role"] == "assistant"
    assert data["message"]["content"]


async def test_chat_requires_at_least_one_message(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/ai/chat", json={"messages": [], "locale": "en"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_suggestions_are_localized(api_client: AsyncClient) -> None:
    en = await api_client.get("/api/v1/ai/chat/suggestions", params={"locale": "en"})
    ar = await api_client.get("/api/v1/ai/chat/suggestions", params={"locale": "ar"})

    assert len(en.json()["data"]["suggestions"]) == 3
    assert en.json()["data"]["suggestions"] != ar.json()["data"]["suggestions"]


async def _frame_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/inventory", params={"category": "frame"})
    return response.json()["data"][0]["id"]


async def _patient_id(client: AsyncClient, name_en: str) -> str:
    response = await client.get("/api/v1/patients", params={"pageSize": 100})
    return next(p["id"] for p in response.json()["data"] if p["nameEn"] == name_en)


async def test_styling_advice_returns_tips(api_client: AsyncClient) -> None:
    frame_id = await _frame_id(api_client)

    response = await api_client.post(
        "/api/v1/ai/styling-advice",
        json={"frameId": frame_id, "need": ProductNeed.EYEGLASSES.value, "locale": "en"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usedFallback"] is True
    assert 2 <= len(data["tips"]) <= 3


async def test_styling_advice_with_patient_context(api_client: AsyncClient) -> None:
    frame_id = await _frame_id(api_client)
    patient_id = await _patient_id(api_client, "Layla Haidar")

    response = await api_client.post(
        "/api/v1/ai/styling-advice",
        json={"patientId": patient_id, "frameId": frame_id, "need": "sunglasses"},
    )

    assert response.status_code == 200


async def test_styling_advice_unknown_frame_is_rejected(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/ai/styling-advice",
        json={"frameId": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_styling_advice_unknown_patient_returns_not_found(
    api_client: AsyncClient,
) -> None:
    frame_id = await _frame_id(api_client)

    response = await api_client.post(
        "/api/v1/ai/styling-advice",
        json={
            "patientId": "00000000-0000-0000-0000-000000000000",
            "frameId": frame_id,
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "patient.notFound"


async def test_ai_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ai/chat/suggestions")

    assert response.status_code == 401
