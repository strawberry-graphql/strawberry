from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, List, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver

    from .exception_source import ExceptionSource


class ConflictingArgumentsError(StrawberryException):
    def __init__(
        self,
        resolver: StrawberryResolver,
        arguments: List[str],
    ) -> None:
        self.function = resolver.wrapped_func
        self.argument_names = arguments

        self.message = (
            f"Arguments {self.argument_names_str} define conflicting resources. "
            "Only one of these arguments may be defined per resolver."
        )

        self.rich_message = self.message

        self.suggestion = (
            f"Only one of {self.argument_names_str} may be defined per resolver."
        )

        self.annotation_message = self.suggestion

    @cached_property
    def argument_names_str(self) -> str:
        return (
            ", ".join(f'"{name}"' for name in self.argument_names[:-1])
            + " and "
            + f'"{self.argument_names[-1]}"'
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_argument_from_object(
            self.function,  # type: ignore
            self.argument_names[1],
        )
