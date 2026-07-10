from app.common.error_codes import ErrorCode
from app.common.pagination import PaginationMeta
from app.common.schema import CamelModel


class ErrorDetail(CamelModel):
    field: str
    message: str


class ErrorInfo(CamelModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class Meta(CamelModel):
    pagination: PaginationMeta | None = None


class Envelope[DataT](CamelModel):
    success: bool
    data: DataT | None = None
    error: ErrorInfo | None = None
    meta: Meta | None = None


def ok[DataT](data: DataT, meta: Meta | None = None) -> Envelope[DataT]:
    return Envelope[DataT](success=True, data=data, meta=meta)


def fail(
    code: ErrorCode | str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> Envelope[None]:
    return Envelope[None](
        success=False,
        error=ErrorInfo(code=str(code), message=message, details=details),
    )
