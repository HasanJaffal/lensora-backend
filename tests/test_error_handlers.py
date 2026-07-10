from collections.abc import AsyncIterator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.common.envelope import Envelope, ok
from app.common.error_codes import ErrorCode
from app.common.exceptions import NotFoundError
from app.common.handlers import register_exception_handlers
from app.common.schema import CamelModel


class _EchoRequest(CamelModel):
    patient_name: str


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> Envelope[None]:
        raise NotFoundError("Patient not found", code=ErrorCode.PATIENT_NOT_FOUND)

    @app.get("/crash")
    async def crash() -> Envelope[None]:
        raise RuntimeError("leaked-internal-detail")

    @app.post("/echo")
    async def echo(body: _EchoRequest) -> Envelope[_EchoRequest]:
        return ok(body)

    return app


@pytest_asyncio.fixture
async def error_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=_build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_app_error_maps_to_status_and_code(error_client: AsyncClient) -> None:
    response = await error_client.get("/boom")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "patient.notFound"
    assert body["error"]["message"] == "Patient not found"


async def test_unexpected_error_is_masked_as_500_envelope(error_client: AsyncClient) -> None:
    response = await error_client.get("/crash")

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "server.internal"
    assert "leaked-internal-detail" not in body["error"]["message"]


async def test_validation_error_returns_field_details(error_client: AsyncClient) -> None:
    response = await error_client.post("/echo", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation.error"
    fields = {detail["field"] for detail in body["error"]["details"]}
    assert "patientName" in fields
