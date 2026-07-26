import uuid

import pytest
from httpx import AsyncClient

from app.features.attachments.service import MAX_ATTACHMENT_SIZE_BYTES
from app.storage.folders import AttachmentFolder
from tests.fake_object_storage import FakeObjectStorage

_PDF_UPLOAD = {
    "subfolder": AttachmentFolder.PATIENT_DOCUMENTS.value,
    "originalFileName": "referral.pdf",
    "contentType": "application/pdf",
    "sizeBytes": 2048,
}


async def _authorize(client: AsyncClient, **overrides: object) -> dict[str, object]:
    response = await client.post(
        "/api/v1/attachments/upload-authorizations", json={**_PDF_UPLOAD, **overrides}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


async def test_authorize_upload_returns_signed_url_and_pending_metadata(
    attachments_client: AsyncClient, object_storage: FakeObjectStorage
) -> None:
    data = await _authorize(attachments_client)

    assert data["uploadUrl"].startswith("https://storage.test/")
    attachment = data["attachment"]
    assert attachment["originalFileName"] == "referral.pdf"
    assert attachment["contentType"] == "application/pdf"
    assert attachment["sizeBytes"] == 2048
    assert attachment["subfolder"] == AttachmentFolder.PATIENT_DOCUMENTS.value
    assert attachment["isUploaded"] is False
    assert object_storage.authorized_paths == [attachment["storagePath"]]


async def test_storage_path_is_organization_scoped_and_uses_the_requested_subfolder(
    attachments_client: AsyncClient, seeded_admin: object
) -> None:
    data = await _authorize(attachments_client)

    organization_segment, subfolder_segment, file_segment = data["attachment"][
        "storagePath"
    ].split("/")
    assert uuid.UUID(organization_segment)
    assert subfolder_segment == AttachmentFolder.PATIENT_DOCUMENTS.value
    assert file_segment.endswith("-referral.pdf")


async def test_authorize_upload_rejects_unknown_subfolder(
    attachments_client: AsyncClient,
) -> None:
    response = await attachments_client.post(
        "/api/v1/attachments/upload-authorizations",
        json={**_PDF_UPLOAD, "subfolder": "../../etc"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_authorize_upload_rejects_unsupported_content_type(
    attachments_client: AsyncClient,
) -> None:
    response = await attachments_client.post(
        "/api/v1/attachments/upload-authorizations",
        json={**_PDF_UPLOAD, "contentType": "application/x-msdownload"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "attachment.unsupportedType"


async def test_authorize_upload_rejects_oversized_file(
    attachments_client: AsyncClient,
) -> None:
    response = await attachments_client.post(
        "/api/v1/attachments/upload-authorizations",
        json={**_PDF_UPLOAD, "sizeBytes": MAX_ATTACHMENT_SIZE_BYTES + 1},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "attachment.fileTooLarge"


@pytest.mark.parametrize(
    "traversal_name",
    ["../../../escape.pdf", "..\\..\\escape.pdf", "/etc/passwd"],
)
async def test_traversal_in_file_name_cannot_escape_the_organization_folder(
    attachments_client: AsyncClient, traversal_name: str
) -> None:
    data = await _authorize(attachments_client, originalFileName=traversal_name)

    storage_path = data["attachment"]["storagePath"]
    assert ".." not in storage_path
    assert len(storage_path.split("/")) == 3
    assert data["attachment"]["originalFileName"] == traversal_name


async def test_confirm_upload_marks_the_attachment_uploaded(
    attachments_client: AsyncClient,
) -> None:
    attachment_id = (await _authorize(attachments_client))["attachment"]["id"]

    response = await attachments_client.post(f"/api/v1/attachments/{attachment_id}/confirm")

    assert response.status_code == 200
    assert response.json()["data"]["isUploaded"] is True


async def test_signed_url_is_issued_for_a_stored_attachment(
    attachments_client: AsyncClient,
) -> None:
    attachment = (await _authorize(attachments_client))["attachment"]

    response = await attachments_client.get(
        f"/api/v1/attachments/{attachment['id']}/signed-url"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert attachment["storagePath"] in data["url"]
    assert data["expiresIn"] == 3600


async def test_listing_returns_only_the_requested_subfolder(
    attachments_client: AsyncClient,
) -> None:
    await _authorize(attachments_client)
    await _authorize(
        attachments_client,
        subfolder=AttachmentFolder.REPORTS.value,
        originalFileName="annual.pdf",
    )

    response = await attachments_client.get(
        "/api/v1/attachments", params={"subfolder": AttachmentFolder.REPORTS.value}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["originalFileName"] for item in data] == ["annual.pdf"]


async def test_delete_removes_both_the_object_and_the_metadata(
    attachments_client: AsyncClient, object_storage: FakeObjectStorage
) -> None:
    attachment = (await _authorize(attachments_client))["attachment"]
    await object_storage.upload(
        attachment["storagePath"], content=b"pdf-bytes", content_type="application/pdf"
    )

    response = await attachments_client.delete(f"/api/v1/attachments/{attachment['id']}")

    assert response.status_code == 200
    assert object_storage.deleted_paths == [attachment["storagePath"]]
    assert attachment["storagePath"] not in object_storage.objects

    follow_up = await attachments_client.get(
        f"/api/v1/attachments/{attachment['id']}/signed-url"
    )
    assert follow_up.status_code == 404
    assert follow_up.json()["error"]["code"] == "attachment.notFound"


async def test_metadata_survives_a_failed_storage_delete(
    attachments_client: AsyncClient, object_storage: FakeObjectStorage
) -> None:
    """A storage failure must not orphan the object by dropping its only pointer."""
    attachment = (await _authorize(attachments_client))["attachment"]
    object_storage.fail_next_delete = True

    response = await attachments_client.delete(f"/api/v1/attachments/{attachment['id']}")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "storage.operationFailed"

    still_there = await attachments_client.get(
        f"/api/v1/attachments/{attachment['id']}/signed-url"
    )
    assert still_there.status_code == 200


async def test_unknown_attachment_returns_not_found(attachments_client: AsyncClient) -> None:
    response = await attachments_client.get(
        f"/api/v1/attachments/{uuid.uuid4()}/signed-url"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "attachment.notFound"


async def test_attachment_routes_require_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/attachments/upload-authorizations", json=_PDF_UPLOAD
    )

    assert response.status_code == 401
