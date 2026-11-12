
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class RespuestaPaginada(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int
