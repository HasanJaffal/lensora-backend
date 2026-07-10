from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.envelope import Envelope, ErrorDetail, fail
from app.common.error_codes import ErrorCode
from app.common.exceptions import AppError


def _envelope_response(status_code: int, envelope: Envelope[None]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder(envelope, by_alias=True))


def _field_from_location(location: tuple[object, ...]) -> str:
    parts = [str(part) for part in location if part not in ("body", "query", "path", "header")]
    return ".".join(parts) if parts else "_root"


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return _envelope_response(exc.http_status, fail(exc.code, exc.message, exc.details))


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(field=_field_from_location(error["loc"]), message=error["msg"])
        for error in exc.errors()
    ]
    envelope = fail(ErrorCode.VALIDATION_ERROR, "Request validation failed", details)
    return _envelope_response(HTTPStatus.UNPROCESSABLE_ENTITY, envelope)


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    envelope = fail(ErrorCode.SERVER_INTERNAL, "An unexpected error occurred")
    return _envelope_response(HTTPStatus.INTERNAL_SERVER_ERROR, envelope)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
