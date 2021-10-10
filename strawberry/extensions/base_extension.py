from typing import Any, Dict

from strawberry.types import ExecutionContext, Info
from strawberry.utils.await_maybe import AwaitableOrValue


class Extension:
    execution_context: ExecutionContext

    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

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

    def resolve(
        self, _next, root, info: Info, *args, **kwargs
    ) -> AwaitableOrValue[None]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[Dict[str, Any]]:
        return {}
