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

    # Patients
    PATIENT_NOT_FOUND = "patient.notFound"

    # Inventory
    INVENTORY_OUT_OF_STOCK = "inventory.outOfStock"

    # AI
    AI_UNAVAILABLE = "ai.unavailable"
