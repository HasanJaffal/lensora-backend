from app.common.envelope import ErrorDetail, fail, ok
from app.common.error_codes import ErrorCode
from app.common.pagination import PaginationMeta
from app.common.schema import CamelModel


class _SampleDto(CamelModel):
    full_name: str


def test_ok_serializes_success_envelope_with_camel_case() -> None:
    envelope = ok(_SampleDto(full_name="Layla"))
    dumped = envelope.model_dump(by_alias=True)

    assert dumped == {
        "success": True,
        "data": {"fullName": "Layla"},
        "error": None,
        "meta": None,
    }


def test_fail_carries_code_and_field_details() -> None:
    envelope = fail(
        ErrorCode.PATIENT_NOT_FOUND,
        "Patient not found",
        [ErrorDetail(field="id", message="unknown patient")],
    )
    dumped = envelope.model_dump(by_alias=True)

    assert dumped["success"] is False
    assert dumped["data"] is None
    assert dumped["error"]["code"] == "patient.notFound"
    assert dumped["error"]["details"] == [{"field": "id", "message": "unknown patient"}]


def test_pagination_meta_computes_total_pages_and_camel_case() -> None:
    meta = PaginationMeta.build(page=2, page_size=20, total=45)

    assert meta.total_pages == 3
    assert meta.model_dump(by_alias=True) == {
        "page": 2,
        "pageSize": 20,
        "total": 45,
        "totalPages": 3,
    }
