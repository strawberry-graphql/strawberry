from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Set

from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types import ExecutionContext


class Extension:
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
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}


Hook = Callable[[Extension], AsyncIteratorOrIterator[None]]

HOOK_METHODS: Set[str] = {
    Extension.on_operation.__name__,
    Extension.on_validate.__name__,
    Extension.on_parse.__name__,
    Extension.on_execute.__name__,
}
