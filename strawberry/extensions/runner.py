import inspect
from typing import Any, Dict, List

from graphql import MiddlewareManager

from strawberry.extensions.constants import SYNC_CONTEXT_WARNING
from strawberry.extensions.context import (
    ParsingContextManager,
    RequestContextManager,
    ValidationContextManager,
)
from strawberry.types import ExecutionContext

from . import Extension


class ExtensionsRunner:
    extensions: List[Extension]

    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: List[Extension] = None,
    ):
        self.execution_context = execution_context
        self.extensions = extensions or []

    def request(self) -> RequestContextManager:
        return RequestContextManager(self)

    def validation(self) -> ValidationContextManager:
        return ValidationContextManager(self)

    def parsing(self) -> ParsingContextManager:
        return ParsingContextManager(self)

    def run_on_all_extensions(self, method_name: str, *args, **kwargs):
        for extension in self.extensions:
            method = getattr(extension, method_name)

            if inspect.iscoroutinefunction(method):
                raise RuntimeError(SYNC_CONTEXT_WARNING)

            method(*args, **kwargs)

    async def run_on_all_extensions_async(self, method_name: str, *args, **kwargs):
        for extension in self.extensions:
            result = getattr(extension, method_name)(*args, **kwargs)

            if inspect.isawaitable(result):
                await result

    def get_extensions_results(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            if inspect.iscoroutinefunction(extension.get_results):
                raise RuntimeError(SYNC_CONTEXT_WARNING)

            data.update(extension.get_results())  # type: ignore

        return data

    async def get_extensions_results_async(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            results = extension.get_results()

            if inspect.isawaitable(results):
                results = await results  # type: ignore

            data.update(results)  # type: ignore

        return data

    def as_middleware_manager(self, *additional_middlewares) -> MiddlewareManager:
        middlewares = tuple(self.extensions) + additional_middlewares

        return MiddlewareManager(*middlewares)
