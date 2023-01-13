from __future__ import annotations

from typing import Any, Callable, Dict

from graphql import GraphQLResolveInfo

from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue


class Extension:
    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def on_operation(self) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after a GraphQL operation (query / mutation) starts"""
        yield None

    def on_validate(self) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the validation step"""
        yield None

    def on_parse(self) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the parsing step"""
        yield None

    def on_execute(self) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the execution step"""
        yield None

    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}


_EXTENSION_FILENAME = (
    __file__  # this is just for testing ease. we could just inspect...
)
Hook = Callable[[Extension], AsyncIteratorOrIterator[None]]
