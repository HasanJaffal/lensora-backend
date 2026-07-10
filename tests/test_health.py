from httpx import AsyncClient


async def test_health_returns_ok_envelope(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"status": "ok"}
    assert body["error"] is None
    assert body["meta"] is None
