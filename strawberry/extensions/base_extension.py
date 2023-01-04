from typing import TYPE_CHECKING, Any, Dict

from graphql import GraphQLResolveInfo

from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue


# just for getting function nams dynamically and editors auto-complete.
class _ExtensionHinter:
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


class Extension:
    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}


if TYPE_CHECKING:

    class Extension(_ExtensionHinter):  # type: ignore # noqa: F811
        def __init__(self, *, execution_context: ExecutionContext):
            self.execution_context = execution_context

        def resolve(
            self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
        ) -> AwaitableOrValue[object]:
            return _next(root, info, *args, **kwargs)

        def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
            return {}
