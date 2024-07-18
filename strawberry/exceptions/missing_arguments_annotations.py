from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, List, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver

    from .exception_source import ExceptionSource


class MissingArgumentsAnnotationsError(StrawberryException):
    """The field is missing the annotation for one or more arguments."""

    def __init__(
        self,
        resolver: StrawberryResolver,
        arguments: List[str],
    ) -> None:
        self.missing_arguments = arguments
        self.function = resolver.wrapped_func
        self.argument_name = arguments[0]

        self.message = (
            f"Missing annotation for {self.missing_arguments_str} "
            f'in field "{resolver.name}", did you forget to add it?'
        )
        self.rich_message = (
            f"Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{resolver.name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add an annotation to the argument "
            f"like so [italic]`{self.missing_arguments[0]}: str`"
        )

        first = "first " if len(self.missing_arguments) > 1 else ""

        self.annotation_message = f"{first}argument missing annotation"

    @property
    def missing_arguments_str(self) -> str:
        arguments = self.missing_arguments

        if len(arguments) == 1:
            return f'argument "{arguments[0]}"'

        head = ", ".join(arguments[:-1])
        return f'arguments "{head}" and "{arguments[-1]}"'

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_argument_from_object(
            self.function,  # type: ignore
            self.argument_name,
        )
