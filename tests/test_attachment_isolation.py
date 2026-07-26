import uuid

from httpx import AsyncClient

from app.storage.folders import AttachmentFolder
from app.storage.paths import (
    build_storage_path,
    is_within_organization,
    sanitize_file_name,
)
from tests.fake_object_storage import FakeObjectStorage

_UPLOAD = {
    "subfolder": AttachmentFolder.PATIENT_IMAGES.value,
    "originalFileName": "scan.png",
    "contentType": "image/png",
    "sizeBytes": 1024,
}


async def _authorize(client: AsyncClient) -> dict[str, object]:
    response = await client.post("/api/v1/attachments/upload-authorizations", json=_UPLOAD)
    assert response.status_code == 200, response.text
    return response.json()["data"]["attachment"]


async def test_each_organization_writes_under_its_own_prefix(
    org_attachment_clients: tuple[AsyncClient, AsyncClient],
) -> None:
    client_a, client_b = org_attachment_clients

    path_a = str((await _authorize(client_a))["storagePath"])
    path_b = str((await _authorize(client_b))["storagePath"])

    assert path_a.split("/")[0] != path_b.split("/")[0]


async def test_one_organization_cannot_read_anothers_attachment(
    org_attachment_clients: tuple[AsyncClient, AsyncClient],
) -> None:
    client_a, client_b = org_attachment_clients
    attachment_a = await _authorize(client_a)

    response = await client_b.get(f"/api/v1/attachments/{attachment_a['id']}/signed-url")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "attachment.notFound"


async def test_one_organization_cannot_delete_anothers_attachment(
    org_attachment_clients: tuple[AsyncClient, AsyncClient],
    object_storage: FakeObjectStorage,
) -> None:
    client_a, client_b = org_attachment_clients
    attachment_a = await _authorize(client_a)

    response = await client_b.delete(f"/api/v1/attachments/{attachment_a['id']}")

    assert response.status_code == 404
    assert object_storage.deleted_paths == []

    still_readable = await client_a.get(
        f"/api/v1/attachments/{attachment_a['id']}/signed-url"
    )
    assert still_readable.status_code == 200


async def test_one_organization_cannot_confirm_anothers_attachment(
    org_attachment_clients: tuple[AsyncClient, AsyncClient],
) -> None:
    client_a, client_b = org_attachment_clients
    attachment_a = await _authorize(client_a)

    response = await client_b.post(f"/api/v1/attachments/{attachment_a['id']}/confirm")

    assert response.status_code == 404


async def test_listing_never_includes_another_organizations_attachments(
    org_attachment_clients: tuple[AsyncClient, AsyncClient],
) -> None:
    client_a, client_b = org_attachment_clients
    attachment_a = await _authorize(client_a)

    response = await client_b.get(
        "/api/v1/attachments", params={"subfolder": AttachmentFolder.PATIENT_IMAGES.value}
    )

    assert response.status_code == 200
    assert attachment_a["id"] not in [item["id"] for item in response.json()["data"]]


def test_sanitize_file_name_strips_directories_and_unsafe_characters() -> None:
    assert sanitize_file_name("../../etc/passwd") == "passwd"
    assert sanitize_file_name("C:\\Windows\\system32.dll") == "system32.dll"
    assert sanitize_file_name(".hidden") == "hidden"
    assert sanitize_file_name("report v2 (final).pdf") == "report-v2-final-.pdf"
    assert sanitize_file_name("...") == "file"
    assert sanitize_file_name("/") == "file"


def test_build_storage_path_always_nests_under_the_organization() -> None:
    organization_id = uuid.uuid4()

    storage_path = build_storage_path(
        organization_id=organization_id,
        folder=AttachmentFolder.REPORTS,
        original_file_name="../escape.pdf",
    )

    assert str(storage_path).startswith(f"{organization_id}/{AttachmentFolder.REPORTS.value}/")
    assert ".." not in str(storage_path)


def test_is_within_organization_rejects_traversal_and_foreign_prefixes() -> None:
    organization_id = uuid.uuid4()
    other_organization_id = uuid.uuid4()

    assert is_within_organization(f"{organization_id}/reports/file.pdf", organization_id)
    assert not is_within_organization(
        f"{other_organization_id}/reports/file.pdf", organization_id
    )
    assert not is_within_organization(
        f"{organization_id}/../{other_organization_id}/f.pdf", organization_id
    )
    assert not is_within_organization(f"/{organization_id}/reports/f.pdf", organization_id)
    assert not is_within_organization("../secrets.pdf", organization_id)
