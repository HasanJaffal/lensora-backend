from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx

from app.common.exceptions import StorageOperationFailedError, StorageUnavailableError

_SIGNED_URL_PATH_KEYS = ("signedURL", "signedUrl", "url")
_REQUEST_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class SignedUpload:
    """A one-shot authorization for a client to write a single object key."""

    upload_url: str
    storage_path: str


class ObjectStorage(ABC):
    """Contract for the attachment object store.

    Every Supabase Storage call in the application goes through an implementation of this
    interface; feature code depends on the abstraction and never on the HTTP details.
    """

    @abstractmethod
    async def create_signed_upload(
        self, storage_path: str, *, allow_overwrite: bool
    ) -> SignedUpload: ...

    @abstractmethod
    async def create_signed_download_url(self, storage_path: str, *, expires_in: int) -> str: ...

    @abstractmethod
    async def upload(self, storage_path: str, *, content: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def delete(self, storage_path: str) -> None: ...


class SupabaseObjectStorage(ObjectStorage):
    """Supabase Storage backed by its REST API, authenticated with the service role key."""

    def __init__(
        self,
        *,
        project_url: str,
        service_role_key: str,
        bucket: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._storage_base_url = f"{project_url.rstrip('/')}/storage/v1"
        self._service_role_key = service_role_key
        self._bucket = bucket
        self._client = client

    async def create_signed_upload(
        self, storage_path: str, *, allow_overwrite: bool
    ) -> SignedUpload:
        payload = await self._request(
            "POST",
            f"/object/upload/sign/{self._bucket}/{storage_path}",
            headers={"x-upsert": "true"} if allow_overwrite else None,
        )
        return SignedUpload(
            upload_url=self._absolute_signed_url(payload, storage_path),
            storage_path=storage_path,
        )

    async def create_signed_download_url(self, storage_path: str, *, expires_in: int) -> str:
        payload = await self._request(
            "POST",
            f"/object/sign/{self._bucket}/{storage_path}",
            json={"expiresIn": expires_in},
        )
        return self._absolute_signed_url(payload, storage_path)

    async def upload(self, storage_path: str, *, content: bytes, content_type: str) -> None:
        await self._request(
            "POST",
            f"/object/{self._bucket}/{storage_path}",
            content=content,
            headers={"Content-Type": content_type},
        )

    async def delete(self, storage_path: str) -> None:
        await self._request("DELETE", f"/object/{self._bucket}/{storage_path}")

    def _absolute_signed_url(self, payload: object, storage_path: str) -> str:
        if not isinstance(payload, dict):
            raise StorageOperationFailedError(
                f"Supabase Storage returned a non-object response for '{storage_path}'"
            )
        for key in _SIGNED_URL_PATH_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return f"{self._storage_base_url}/{value.lstrip('/')}"
        raise StorageOperationFailedError(
            f"Supabase Storage returned no signed URL for '{storage_path}'"
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: object | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> object:
        request_headers = {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
            **(headers or {}),
        }
        try:
            async with self._session() as client:
                response = await client.request(
                    method,
                    f"{self._storage_base_url}{path}",
                    json=json,
                    content=content,
                    headers=request_headers,
                )
        except httpx.HTTPError as error:
            raise StorageUnavailableError(
                f"Could not reach Supabase Storage: {error}"
            ) from error

        if response.is_error:
            raise StorageOperationFailedError(
                f"Supabase Storage rejected {method} {path} with status {response.status_code}"
            )
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as error:
            raise StorageOperationFailedError(
                f"Supabase Storage returned a malformed response for {method} {path}"
            ) from error

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[httpx.AsyncClient]:
        """Yield the injected client, or a short-lived one when none was supplied.

        An injected client belongs to its caller, so it is never closed here.
        """
        if self._client is not None:
            yield self._client
            return
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            yield client
