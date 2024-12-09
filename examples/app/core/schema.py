
from typing import Any,TypeVar,Generic
from fastapi_crud import AbstractResponseModel
T = TypeVar("T")
class ResponseSchema(AbstractResponseModel,Generic[T]):
    data: T
    msg: str

    @classmethod
    def create(
        cls, content: Any
    ):
        return cls(
            data=content,
            msg="success"
        )