from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from strawberry.exceptions.utils.source_finder import SourceFinder

from .exception import StrawberryException
from .exception_source import ExceptionSource


if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.object_type import TypeDefinition


class UnresolvedFieldTypeError(StrawberryException):
    def __init__(
        self,
        type_definition: TypeDefinition,
        field: StrawberryField,
    ):
        self.type_definition = type_definition
        self.field = field

        self.message = (
            f"Could not resolve the type of '{self.field.name}'. "
            "Check that the class is accessible from the global module scope."
        )

        self.rich_message = (
            f"Could not resolve the type of [underline]'{self.field.name}'[/]. "
            "Check that the class is accessible from the global module scope."
        )
        self.annotation_message = "field defined here"
        self.suggestion = (
            "To fix this error you should either import the type or use LazyType."
        )

        super().__init__(self.message)

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(
            self.type_definition.origin, self.field.name
        )
