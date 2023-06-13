from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Set

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

    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def on_operation(
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover # pyright: ignore
        """Called before and after a GraphQL operation (query / mutation) starts"""
        yield None

    def on_validate(
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover # pyright: ignore
        """Called before and after the validation step"""
        yield None

    def on_parse(
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover # pyright: ignore
        """Called before and after the parsing step"""
        yield None

    def on_execute(
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover # pyright: ignore
        """Called before and after the execution step"""
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

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}


Hook = Callable[[SchemaExtension], AsyncIteratorOrIterator[None]]

HOOK_METHODS: Set[str] = {
    SchemaExtension.on_operation.__name__,
    SchemaExtension.on_validate.__name__,
    SchemaExtension.on_parse.__name__,
    SchemaExtension.on_execute.__name__,
}
