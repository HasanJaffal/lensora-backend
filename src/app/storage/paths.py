import posixpath
import re
import uuid
from dataclasses import dataclass

from app.storage.folders import AttachmentFolder

MAX_STORED_FILE_NAME_LENGTH = 120

_UNSAFE_FILE_NAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_LEADING_DOTS = re.compile(r"^\.+")


@dataclass(frozen=True, slots=True)
class StoragePath:
    """A validated ``{organization_id}/{folder}/{file_name}`` object key."""

    organization_id: uuid.UUID
    folder: AttachmentFolder
    stored_file_name: str

    def __str__(self) -> str:
        return f"{self.organization_id}/{self.folder.value}/{self.stored_file_name}"


def build_storage_path(
    *,
    organization_id: uuid.UUID,
    folder: AttachmentFolder,
    original_file_name: str,
) -> StoragePath:
    """Compose the object key for a new upload.

    The caller-supplied name is sanitized and prefixed with a UUID so that a client can never
    influence the path beyond the final segment, and two uploads of the same name never collide.
    """
    return StoragePath(
        organization_id=organization_id,
        folder=folder,
        stored_file_name=f"{uuid.uuid4()}-{sanitize_file_name(original_file_name)}",
    )


def sanitize_file_name(original_file_name: str) -> str:
    """Reduce a client-supplied filename to a single safe path segment.

    Strips any directory component, replaces characters outside ``[A-Za-z0-9._-]``, and removes
    leading dots so the result can neither traverse (``../``) nor produce a hidden/empty name.
    """
    last_segment = original_file_name.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    safe_name = _UNSAFE_FILE_NAME_CHARS.sub("-", last_segment)
    safe_name = _LEADING_DOTS.sub("", safe_name).strip("-")
    if not safe_name:
        return "file"
    return safe_name[:MAX_STORED_FILE_NAME_LENGTH]


def is_within_organization(storage_path: str, organization_id: uuid.UUID) -> bool:
    """Whether ``storage_path`` resolves inside the organization's folder.

    Normalizes first so a stored value containing ``..`` cannot escape the tenant prefix.
    """
    normalized = posixpath.normpath(storage_path.replace("\\", "/"))
    if normalized.startswith(("/", "../")) or normalized == "..":
        return False
    return normalized.split("/", maxsplit=1)[0] == str(organization_id)
