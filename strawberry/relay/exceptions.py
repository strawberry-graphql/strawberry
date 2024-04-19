from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Type, cast

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.exceptions.exception_source import ExceptionSource
    from strawberry.types.fields.resolver import StrawberryResolver


class NodeIDAnnotationError(StrawberryException):
    def __init__(self, message: str, cls: Type) -> None:
        self.cls = cls

        self.message = message
        self.rich_message = (
            "Expected exactly one `relay.NodeID` annotated field to be "
            f"defined in `[underline]{self.cls.__name__}[/]` type."
        )
        self.suggestion = (
            "To fix this error you should annotate exactly one of your fields "
            "using `relay.NodeID`. That field should be unique among "
            "your type objects (usually its `id` for ORM objects)."
        )
        self.annotation_message = "node missing node id private annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()

        return source_finder.find_class_from_object(self.cls)


class RelayWrongAnnotationError(StrawberryException):
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
            f"like [italic]`{self.field_name}: relay.Connection[{cls}]` "
            f"or [italic]`@relay.connection(relay.Connection[{cls}])`"
        )
        self.annotation_message = "relay wrong annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class RelayWrongResolverAnnotationError(StrawberryException):
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
        self.annotation_message = "relay wrong resolver annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_function_from_object(cast(Callable, self.function))
