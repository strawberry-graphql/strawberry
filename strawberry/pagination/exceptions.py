from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Type, cast

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.exceptions.exception_source import ExceptionSource
    from strawberry.types.fields.resolver import StrawberryResolver


class ConnectionWrongAnnotationError(StrawberryException):
    def __init__(self, field_name: str, cls: Type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f'Wrong annotation used on field "{field_name}". It should be '
            'annotated with a "Connection" subclass.'
        )
        self.rich_message = (
            f"Wrong annotation for field `[underline]{self.field_name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add a valid annotation, "
            f"like [italic]`{self.field_name}: Connection[{cls}]` "
            f"or [italic]`@connection(Connection[{cls}])`"
        )
        self.annotation_message = "connection wrong annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class ConnectionWrongResolverAnnotationError(StrawberryException):
    def __init__(self, field_name: str, resolver: StrawberryResolver) -> None:
        self.function = resolver.wrapped_func
        self.field_name = field_name

        self.message = (
            f'Wrong annotation used on "{field_name}" resolver. '
            "It should be return an iterable or async iterable object."
        )
        self.rich_message = (
            f"Wrong annotation used on `{field_name}` resolver. "
            "It should be return an `iterable` or `async iterable` object."
        )
        self.suggestion = (
            "To fix this error you can annootate your resolver to return "
            "one of the following options: `List[<NodeType>]`, "
            "`Iterator[<NodeType>]`, `Iterable[<NodeType>]`, "
            "`AsyncIterator[<NodeType>]`, `AsyncIterable[<NodeType>]`, "
            "`Generator[<NodeType>, Any, Any]` and "
            "`AsyncGenerator[<NodeType>, Any]`."
        )
        self.annotation_message = "connection wrong resolver annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_function_from_object(cast(Callable, self.function))


__all__ = [
    "ConnectionWrongAnnotationError",
    "ConnectionWrongResolverAnnotationError",
]
