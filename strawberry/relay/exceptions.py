from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Type, Union, cast

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder
from strawberry.utils.cached_property import cached_property

if TYPE_CHECKING:
    from strawberry.exceptions.exception_source import ExceptionSource
    from strawberry.types.fields.resolver import StrawberryResolver


class NodeIDAnnotationError(StrawberryException):
    def __init__(self, message: str, cls: Type):
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
    def __init__(self, field_name: str, resolver: Union[StrawberryResolver, Callable]):
        from strawberry.types.fields.resolver import StrawberryResolver

        self.function = (
            resolver.wrapped_func
            if isinstance(resolver, StrawberryResolver)
            else resolver
        )
        self.field_name = field_name

        self.message = (
            f'Unable to determine the connection type of field "{field_name}". '
            "It should be annotated with a return value of `List[<NodeType>]`, "
            "`Iterable[<NodeType>]`, `Iterator[<NodeType>]`, "
            "`AsyncIterable[<NodeType>]` or `AsyncIterator[<NodeType>]`"
        )
        self.rich_message = (
            f"Wrong annotation for field `[underline]{self.field_name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can annotate the return it using "
            "a return value of `List[<NodeType>]`, "
            "`Iterable[<NodeType>]`, `Iterator[<NodeType>]`, "
            "`AsyncIterable[<NodeType>]` or `AsyncIterator[<NodeType>]`"
        )
        self.annotation_message = "relay custom resolver wrong annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_function_from_object(cast(Callable, self.function))


class RelayWrongNodeResolverAnnotationError(StrawberryException):
    def __init__(self, field_name: str, resolver: Union[StrawberryResolver, Callable]):
        from strawberry.types.fields.resolver import StrawberryResolver

        self.function = (
            resolver.wrapped_func
            if isinstance(resolver, StrawberryResolver)
            else resolver
        )
        self.field_name = field_name

        self.message = (
            f'Unable to determine the connection type of field "{field_name}". '
            "The `node_resolver` function should be annotated with a return value "
            "of `<NodeType>`"
        )
        self.rich_message = (
            "Wrong annotation for field `node_resolver` function used "
            "in the `@relay.connection` decorator of field "
            "[underline]{self.field_name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can annotate the `node_resolver` function "
            "using a return value of `<NodeType>`"
        )
        self.annotation_message = "relay node_resolver wrong annotation"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.function is None:
            return None  # pragma: no cover

        source_finder = SourceFinder()
        return source_finder.find_function_from_object(cast(Callable, self.function))
