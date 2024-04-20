from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional

from strawberry.type import get_object_definition

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.arguments import StrawberryArgument
    from strawberry.types.fields.resolver import StrawberryResolver

    from .exception_source import ExceptionSource


class InvalidArgumentTypeError(StrawberryException):
    def __init__(
        self,
        resolver: StrawberryResolver,
        argument: StrawberryArgument,
    ) -> None:
        from strawberry.union import StrawberryUnion

        self.function = resolver.wrapped_func
        self.argument_name = argument.python_name
        # argument_type: Literal["union", "interface"],

        argument_type = "unknown"

        if isinstance(argument.type, StrawberryUnion):
            argument_type = "union"
        else:
            type_definition = get_object_definition(argument.type)
            if type_definition and type_definition.is_interface:
                argument_type = "interface"

        self.message = (
            f'Argument "{self.argument_name}" on field '
            f'"{resolver.name}" cannot be of type '
            f'"{argument_type}"'
        )
        self.rich_message = self.message

        if argument_type == "union":
            self.suggestion = "Unions are not supported as arguments in GraphQL."
        elif argument_type == "interface":
            self.suggestion = "Interfaces are not supported as arguments in GraphQL."
        else:
            self.suggestion = f"{self.argument_name} is not supported as an argument."

        self.annotation_message = (
            f'Argument "{self.argument_name}" cannot be of type "{argument_type}"'
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_argument_from_object(
            self.function,  # type: ignore
            self.argument_name,
        )
