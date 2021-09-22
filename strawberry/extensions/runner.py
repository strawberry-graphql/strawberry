import inspect
from typing import Any, Dict, List, Optional, Type, Union

from graphql import MiddlewareManager

from strawberry.extensions.context import (
    ParsingContextManager,
    RequestContextManager,
    ValidationContextManager,
)
from strawberry.types import ExecutionContext
from strawberry.utils.await_maybe import await_maybe

from . import Extension


class ExtensionsRunner:
    extensions: List[Extension]

    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: Optional[List[Union[Type[Extension], Extension]]] = None,
    ):
        self.execution_context = execution_context

        if not extensions:
            extensions = []

        init_extensions: List[Extension] = []

        for extension in extensions:
            # If the extension has already been instantiated then set the
            # `execution_context` attribute
            if isinstance(extension, Extension):
                extension.execution_context = execution_context
                init_extensions.append(extension)
            else:
                init_extensions.append(extension(execution_context=execution_context))

        self.extensions = init_extensions

    def request(self) -> RequestContextManager:
        return RequestContextManager(self.extensions)

    def validation(self) -> ValidationContextManager:
        return ValidationContextManager(self.extensions)

    def parsing(self) -> ParsingContextManager:
        return ParsingContextManager(self.extensions)

    def get_extensions_results_sync(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            if inspect.iscoroutinefunction(extension.get_results):
                msg = "Cannot use async extension hook during sync execution"
                raise RuntimeError(msg)

            data.update(extension.get_results())  # type: ignore

        return data

    async def get_extensions_results(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            results = await await_maybe(extension.get_results())
            data.update(results)  # type: ignore

        return data

    def as_middleware_manager(self, *additional_middlewares) -> MiddlewareManager:
        middlewares = tuple(self.extensions) + additional_middlewares

        return MiddlewareManager(*middlewares)
