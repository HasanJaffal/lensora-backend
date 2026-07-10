from math import ceil
from typing import Annotated

from fastapi import Query

from app.common.schema import CamelModel

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageParams:
    """Query-parameter dependency for list endpoints (`?page=1&pageSize=20`)."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[
            int, Query(alias="pageSize", ge=1, le=MAX_PAGE_SIZE)
        ] = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationMeta(CamelModel):
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def build(cls, *, page: int, page_size: int, total: int) -> "PaginationMeta":
        total_pages = ceil(total / page_size) if page_size else 0
        return cls(page=page, page_size=page_size, total=total, total_pages=total_pages)
