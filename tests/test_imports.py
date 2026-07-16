from httpx import AsyncClient

from app.features.import_forms.service import MAX_FILE_SIZE_BYTES

_PNG = ("form.png", b"\x89PNG\r\n\x1a\n fake image bytes", "image/png")
_ALLOWED_ANSWER_TYPES = {"short", "long", "checklist"}


async def test_upload_returns_ready_import_with_typed_questions(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post("/api/v1/imports", files={"file": _PNG})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready"
    assert data["questionCount"] == len(data["questions"])
    assert data["questionCount"] > 0
    assert all(q["answerType"] in _ALLOWED_ANSWER_TYPES for q in data["questions"])


async def test_upload_uses_fallback_when_ai_disabled(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/imports", files={"file": _PNG})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usedFallback"] is True
    assert data["questions"][0]["textAr"]


async def test_upload_rejects_unsupported_type(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/imports",
        files={"file": ("notes.txt", b"just text", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "import.unsupportedType"


async def test_upload_rejects_file_over_20mb(api_client: AsyncClient) -> None:
    oversized = b"\x00" * (MAX_FILE_SIZE_BYTES + 1)

    response = await api_client.post(
        "/api/v1/imports",
        files={"file": ("scan.pdf", oversized, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "import.fileTooLarge"


async def test_get_import_returns_stored_result(api_client: AsyncClient) -> None:
    created = await api_client.post("/api/v1/imports", files={"file": _PNG})
    import_id = created.json()["data"]["id"]

    response = await api_client.get(f"/api/v1/imports/{import_id}")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == import_id


async def test_get_unknown_import_returns_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get(
        "/api/v1/imports/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_use_as_intake_yields_consumable_definition(
    api_client: AsyncClient,
) -> None:
    created = await api_client.post("/api/v1/imports", files={"file": _PNG})
    import_id = created.json()["data"]["id"]

    response = await api_client.post(f"/api/v1/imports/{import_id}/use-as-intake")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["importId"] == import_id
    assert data["questionCount"] == len(data["questions"])
    assert data["questions"]


async def test_imports_require_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/imports", files={"file": _PNG})

    assert response.status_code == 401
