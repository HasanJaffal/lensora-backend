from enum import StrEnum


class ErrorCode(StrEnum):
    """Canonical, dot-namespaced error codes — the contract with the frontend i18n layer.

    Each value MUST stay in sync with the frontend `backend-error-keys.ts`. Treat additions
    and renames as API changes: the frontend translates messages by these keys.
    """

    # Framework / cross-cutting
    VALIDATION_ERROR = "validation.error"
    SERVER_INTERNAL = "server.internal"
    RESOURCE_NOT_FOUND = "resource.notFound"
    RESOURCE_CONFLICT = "resource.conflict"

    # Auth
    AUTH_INVALID_CREDENTIALS = "auth.invalidCredentials"
    AUTH_UNAUTHORIZED = "auth.unauthorized"
    AUTH_SESSION_EXPIRED = "auth.sessionExpired"
    AUTH_ACCOUNT_DISABLED = "auth.accountDisabled"
    AUTH_EMAIL_TAKEN = "auth.emailTaken"

    # Organizations
    ORGANIZATION_SLUG_TAKEN = "organization.slugTaken"
    ORGANIZATION_DEACTIVATED = "organization.deactivated"

    # Tenancy
    TENANT_FORBIDDEN = "tenant.forbidden"

    # Patients
    PATIENT_NOT_FOUND = "patient.notFound"

    # Inventory
    INVENTORY_OUT_OF_STOCK = "inventory.outOfStock"
    INVENTORY_SKU_TAKEN = "inventory.skuTaken"

    # Import
    IMPORT_FILE_TOO_LARGE = "import.fileTooLarge"
    IMPORT_UNSUPPORTED_TYPE = "import.unsupportedType"

    # AI
    AI_UNAVAILABLE = "ai.unavailable"

    # Attachments
    ATTACHMENT_NOT_FOUND = "attachment.notFound"
    ATTACHMENT_INVALID_FOLDER = "attachment.invalidFolder"
    ATTACHMENT_FILE_TOO_LARGE = "attachment.fileTooLarge"
    ATTACHMENT_UNSUPPORTED_TYPE = "attachment.unsupportedType"

    # Storage
    STORAGE_NOT_CONFIGURED = "storage.notConfigured"
    STORAGE_UNAVAILABLE = "storage.unavailable"
    STORAGE_OPERATION_FAILED = "storage.operationFailed"
