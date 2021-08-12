from typing import Any, Awaitable, Dict, Union

from strawberry.types import ExecutionContext, Info


class Extension:
    def __init__(self, *, execution_context: ExecutionContext):
        self.execution_context = execution_context

    def on_request_start(self) -> Union[None, Awaitable[None]]:
        """This method is called when a GraphQL request starts"""

    def on_request_end(self) -> Union[None, Awaitable[None]]:
        """This method is called when a GraphQL request ends"""

    def on_validation_start(self) -> Union[None, Awaitable[None]]:
        """This method is called before the validation step"""

    def on_validation_end(self) -> Union[None, Awaitable[None]]:
        """This method is called after the validation step"""

    def on_parsing_start(self) -> Union[None, Awaitable[None]]:
        """This method is called before the parsing step"""

    def on_parsing_end(self) -> Union[None, Awaitable[None]]:
        """This method is called after the parsing step"""

    def resolve(
        self, _next, root, info: Info, *args, **kwargs
    ) -> Union[None, Awaitable[None]]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> Union[Dict[str, Any], Awaitable[Dict[str, Any]]]:
        return {}
