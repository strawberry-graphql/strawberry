from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types import ExecutionContext


class LifecycleStep(Enum):
    OPERATION = "operation"
    VALIDATION = "validation"
    PARSE = "parse"
    RESOLVE = "resolve"


class SchemaExtension:
    execution_context: ExecutionContext

    # to support extensions that still use the old signature
    # we have an optional argument here for ease of initialization.
    def __init__(
        self, *, execution_context: ExecutionContext | None = None
    ) -> None: ...
    def on_operation(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after a GraphQL operation (query / mutation) starts."""
        yield None

    def on_validate(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the validation step."""
        yield None

    def on_parse(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the parsing step."""
        yield None

    def on_execute(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the execution step."""
        yield None

    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[dict[str, Any]]:
        return {}

    @classmethod
    def _implements_resolve(cls) -> bool:
        """Whether the extension implements the resolve method."""
        return cls.resolve is not SchemaExtension.resolve


Hook = Callable[[SchemaExtension], AsyncIteratorOrIterator[None]]

HOOK_METHODS: set[str] = {
    SchemaExtension.on_operation.__name__,
    SchemaExtension.on_validate.__name__,
    SchemaExtension.on_parse.__name__,
    SchemaExtension.on_execute.__name__,
}

__all__ = ["HOOK_METHODS", "Hook", "LifecycleStep", "SchemaExtension"]
