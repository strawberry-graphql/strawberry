from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from collections.abc import Iterable

    from strawberry.types.base import StrawberryObjectDefinition

    from .exception_source import ExceptionSource


class InvalidSuperclassInterfaceError(StrawberryException):
    def __init__(
        self,
        cls: type[type],
        input_name: str,
        interfaces: Iterable[StrawberryObjectDefinition],
    ) -> None:
        self.cls = cls
        pretty_interface_names = ", ".join(interface.name for interface in interfaces)

        self.message = self.rich_message = (
            f"Input class {input_name!r} cannot inherit "
            f"from interface(s): {pretty_interface_names}"
        )

        self.annotation_message = "input type class defined here"

        self.suggestion = "To fix this error, make sure your input type class does not inherit from any interfaces."

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        source_finder = SourceFinder()
        return source_finder.find_class_from_object(self.cls)
