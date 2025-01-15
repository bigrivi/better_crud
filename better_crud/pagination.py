from __future__ import annotations

import math
from typing import Generic, Sequence, TypeVar, Optional, Any
from fastapi import Query
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from pydantic import BaseModel


T = TypeVar('T')


class Params(BaseModel, AbstractParams):
    page: Optional[int] = Query(default=None, gte=0, description='Page number')
    size: Optional[int] = Query(
        default=None,
        gte=0,
        le=100,
        description='Page size'
    )

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )


class Page(AbstractPage[T], Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int
    __params_type__ = Params

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> Page[T]:
        size = params.size if params.size is not None else (total or None)
        page = params.page if params.page is not None else 1
        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = math.ceil(total / size)
        else:
            pages = None
        return cls(items=items, total=total, page=page, size=size, pages=pages)
