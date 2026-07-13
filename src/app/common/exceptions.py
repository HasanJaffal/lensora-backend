from http import HTTPStatus

from app.common.envelope import ErrorDetail
from app.common.error_codes import ErrorCode


class AppError(Exception):
    """Base for all domain errors. Handlers convert these into the error envelope.

    Subclasses fix the HTTP status and a default code; callers pass a more specific code
    (e.g. `PATIENT_NOT_FOUND`) and message at the raise site.
    """

    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    default_code: ErrorCode = ErrorCode.SERVER_INTERNAL

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | str | None = None,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = str(code) if code is not None else str(self.default_code)
        self.details = details


class ValidationError(AppError):
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY
    default_code = ErrorCode.VALIDATION_ERROR


class NotFoundError(AppError):
    http_status = HTTPStatus.NOT_FOUND
    default_code = ErrorCode.RESOURCE_NOT_FOUND


class ConflictError(AppError):
    http_status = HTTPStatus.CONFLICT
    default_code = ErrorCode.RESOURCE_CONFLICT


class UnauthorizedError(AppError):
    http_status = HTTPStatus.UNAUTHORIZED
    default_code = ErrorCode.AUTH_UNAUTHORIZED


class InvalidCredentialsError(UnauthorizedError):
    default_code = ErrorCode.AUTH_INVALID_CREDENTIALS


class SessionExpiredError(UnauthorizedError):
    default_code = ErrorCode.AUTH_SESSION_EXPIRED


class AccountDisabledError(AppError):
    http_status = HTTPStatus.FORBIDDEN
    default_code = ErrorCode.AUTH_ACCOUNT_DISABLED


class PatientNotFoundError(NotFoundError):
    default_code = ErrorCode.PATIENT_NOT_FOUND


class OutOfStockError(ConflictError):
    default_code = ErrorCode.INVENTORY_OUT_OF_STOCK


class AIUnavailableError(AppError):
    http_status = HTTPStatus.SERVICE_UNAVAILABLE
    default_code = ErrorCode.AI_UNAVAILABLE
