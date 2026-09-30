from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic

import strawberry

if TYPE_CHECKING:
    from .book import Book


@strawberry.pydantic.type
class Author(pydantic.BaseModel):
    name: str
    books: list[Book] = []
