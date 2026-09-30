from __future__ import annotations

import pydantic

import strawberry

from .author import Author


@strawberry.pydantic.type
class Book(pydantic.BaseModel):
    title: str
    author: Author | None = None


# Author can only be completed once Book is defined, as pydantic documents for
# models that import each other
Author.model_rebuild()
