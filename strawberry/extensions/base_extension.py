from typing import Any, Dict

from graphql import GraphQLResolveInfo

from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue


class Extension:
    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def on_request(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after a GraphQL request starts"""

    def on_validate(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the validation step"""

    def on_parse(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the parsing step"""

    def on_execute(self) -> AsyncIteratorOrIterator[None]:
        """Called before and after the execution step"""

    def resolve(
        self, _next, root, info: GraphQLResolveInfo, *args, **kwargs
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}
