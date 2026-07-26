import httpx
import pytest

from app.common.exceptions import (
    StorageNotConfiguredError,
    StorageOperationFailedError,
    StorageUnavailableError,
)
from app.core.config import Settings
from app.storage import deps
from app.storage.client import SupabaseObjectStorage

_PROJECT_URL = "https://project.supabase.co"
_SERVICE_ROLE_KEY = "service-role-key"
_BUCKET = "attachments"
_PATH = "org-1/reports/annual.pdf"


def _storage(handler: object) -> SupabaseObjectStorage:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return SupabaseObjectStorage(
        project_url=_PROJECT_URL,
        service_role_key=_SERVICE_ROLE_KEY,
        bucket=_BUCKET,
        client=httpx.AsyncClient(transport=transport),
    )


async def test_signed_upload_url_is_absolute_and_service_key_authenticated() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["apikey"] = request.headers.get("apikey")
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(
            200, json={"url": f"/object/upload/sign/{_BUCKET}/{_PATH}?token=abc"}
        )

    signed_upload = await _storage(handler).create_signed_upload(_PATH, allow_overwrite=False)

    assert seen["url"] == f"{_PROJECT_URL}/storage/v1/object/upload/sign/{_BUCKET}/{_PATH}"
    assert seen["apikey"] == _SERVICE_ROLE_KEY
    assert seen["authorization"] == f"Bearer {_SERVICE_ROLE_KEY}"
    assert signed_upload.upload_url == (
        f"{_PROJECT_URL}/storage/v1/object/upload/sign/{_BUCKET}/{_PATH}?token=abc"
    )
    assert signed_upload.storage_path == _PATH


async def test_signed_download_url_sends_the_requested_expiry() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content"] = request.content
        return httpx.Response(200, json={"signedURL": f"/object/sign/{_BUCKET}/{_PATH}?token=x"})

    url = await _storage(handler).create_signed_download_url(_PATH, expires_in=900)

    assert b'"expiresIn":900' in bytes(seen["content"])  # type: ignore[arg-type]
    assert url == f"{_PROJECT_URL}/storage/v1/object/sign/{_BUCKET}/{_PATH}?token=x"


async def test_delete_issues_a_delete_against_the_object_path() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"message": "Successfully deleted"})

    await _storage(handler).delete(_PATH)

    assert seen["method"] == "DELETE"
    assert seen["url"] == f"{_PROJECT_URL}/storage/v1/object/{_BUCKET}/{_PATH}"


async def test_upload_posts_the_bytes_with_their_content_type() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content"] = request.content
        seen["content_type"] = request.headers.get("content-type")
        return httpx.Response(200, json={"Key": f"{_BUCKET}/{_PATH}"})

    await _storage(handler).upload(_PATH, content=b"pdf-bytes", content_type="application/pdf")

    assert seen["content"] == b"pdf-bytes"
    assert seen["content_type"] == "application/pdf"


async def test_error_status_raises_a_typed_storage_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "Unauthorized"})

    with pytest.raises(StorageOperationFailedError):
        await _storage(handler).delete(_PATH)


async def test_missing_signed_url_in_response_raises_rather_than_returning_a_bad_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    with pytest.raises(StorageOperationFailedError):
        await _storage(handler).create_signed_upload(_PATH, allow_overwrite=False)


async def test_transport_failure_surfaces_as_storage_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(StorageUnavailableError):
        await _storage(handler).create_signed_download_url(_PATH, expires_in=60)


async def test_overwrite_flag_sets_the_upsert_header() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["x-upsert"] = request.headers.get("x-upsert")
        return httpx.Response(200, json={"url": f"/object/upload/sign/{_BUCKET}/{_PATH}"})

    await _storage(handler).create_signed_upload(_PATH, allow_overwrite=True)

    assert seen["x-upsert"] == "true"


def test_object_storage_refuses_to_build_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing configuration must fail loudly rather than silently dropping uploads."""
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: Settings(SUPABASE_URL=None, SUPABASE_SERVICE_ROLE_KEY=None),
    )
    deps.get_object_storage.cache_clear()

    with pytest.raises(StorageNotConfiguredError):
        deps.get_object_storage()

    deps.get_object_storage.cache_clear()


def test_object_storage_is_built_when_credentials_are_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: Settings(
            SUPABASE_URL=_PROJECT_URL,
            SUPABASE_SERVICE_ROLE_KEY=_SERVICE_ROLE_KEY,
            SUPABASE_STORAGE_BUCKET=_BUCKET,
        ),
    )
    deps.get_object_storage.cache_clear()

    assert isinstance(deps.get_object_storage(), SupabaseObjectStorage)

    deps.get_object_storage.cache_clear()
