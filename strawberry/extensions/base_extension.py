from typing import Any, Dict

from graphql import GraphQLResolveInfo

from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue


class ExtensionLegacy:
    DEPRECATION_MESSAGE = (
        "Event driven styled extensions are deprecated, use %s instead"
    )

    def on_request_start(self) -> AwaitableOrValue[None]:
        """This method is called when a GraphQL request starts"""

    def on_request_end(self) -> AwaitableOrValue[None]:
        """This method is called when a GraphQL request ends"""

    def on_validation_start(self) -> AwaitableOrValue[None]:
        """This method is called before the validation step"""

    def on_validation_end(self) -> AwaitableOrValue[None]:
        """This method is called after the validation step"""

    def on_parsing_start(self) -> AwaitableOrValue[None]:
        """This method is called before the parsing step"""

    def on_parsing_end(self) -> AwaitableOrValue[None]:
        """This method is called after the parsing step"""

    def on_executing_start(self) -> AwaitableOrValue[None]:
        """This method is called before the execution step"""

    def on_executing_end(self) -> AwaitableOrValue[None]:
        """This method is called after the executing step"""


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
