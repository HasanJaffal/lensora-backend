from dataclasses import dataclass

from app.common.exceptions import StorageOperationFailedError
from app.storage.client import ObjectStorage, SignedUpload

SIGNED_URL_HOST = "https://storage.test/storage/v1"


@dataclass
class StoredObject:
    content: bytes
    content_type: str


class FakeObjectStorage(ObjectStorage):
    """In-memory stand-in for Supabase Storage.

    Keeps the tests deterministic and network-free while exercising the same contract the
    Supabase implementation honors.
    """

    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}
        self.authorized_paths: list[str] = []
        self.deleted_paths: list[str] = []
        self.fail_next_delete = False

    async def create_signed_upload(
        self, storage_path: str, *, allow_overwrite: bool
    ) -> SignedUpload:
        self.authorized_paths.append(storage_path)
        return SignedUpload(
            upload_url=f"{SIGNED_URL_HOST}/object/upload/sign/{storage_path}?token=fake-upload",
            storage_path=storage_path,
        )

    async def create_signed_download_url(self, storage_path: str, *, expires_in: int) -> str:
        return f"{SIGNED_URL_HOST}/object/sign/{storage_path}?token=fake&expiresIn={expires_in}"

    async def upload(self, storage_path: str, *, content: bytes, content_type: str) -> None:
        self.objects[storage_path] = StoredObject(content=content, content_type=content_type)

    async def delete(self, storage_path: str) -> None:
        if self.fail_next_delete:
            self.fail_next_delete = False
            raise StorageOperationFailedError(f"Simulated storage failure for '{storage_path}'")
        self.deleted_paths.append(storage_path)
        self.objects.pop(storage_path, None)
