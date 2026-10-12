from __future__ import annotations

import sys
from functools import cached_property
from typing import TYPE_CHECKING

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.types.base import StrawberryObjectDefinition

    from .exception_source import ExceptionSource


class UndecoratedSubclassError(StrawberryException):
    """An undecorated subclass of a Strawberry type used in the schema.

    Python inherits `__strawberry_definition__`, so the subclass would be
    published as its parent type, without any field it declares itself.

    `parent` is the closest base class with its own Strawberry definition.
    """

    def __init__(
        self,
        cls: type,
        parent: type,
        parent_definition: StrawberryObjectDefinition,
    ) -> None:
        self.cls = cls
        self.parent = parent

        if parent_definition.is_input:
            kind, decorator = "input type", "input"
        elif parent_definition.is_interface:
            kind, decorator = "interface", "type"
        else:
            kind, decorator = "type", "type"

        decorator = (
            f"@strawberry.pydantic.{decorator}"
            if _is_pydantic_model(parent)
            else f"@strawberry.{decorator}"
        )

        self.message = (
            f"`{cls.__name__}` subclasses the Strawberry {kind} "
            f"`{parent.__name__}` but isn't decorated itself, so it can't be "
            "used in the schema"
        )
        self.rich_message = (
            f"`[underline]{cls.__name__}[/]` subclasses the Strawberry {kind} "
            f"`[underline]{parent.__name__}[/]` but isn't decorated itself, so "
            "it can't be used in the schema"
        )
        self.annotation_message = "undecorated class defined here"
        self.suggestion = (
            f"Decorate `{cls.__name__}` with `{decorator}`, or use "
            f"`{parent.__name__}` instead of `{cls.__name__}` in your annotations. "
            f"Otherwise `{cls.__name__}` would be published as "
            f"`{parent.__name__}`, without the fields it declares itself."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()
        return source_finder.find_class_from_object(self.cls)


def _is_pydantic_model(cls: type) -> bool:
    # pydantic is optional, and a model's module has imported it
    pydantic = sys.modules.get("pydantic")

    return pydantic is not None and issubclass(cls, pydantic.BaseModel)
