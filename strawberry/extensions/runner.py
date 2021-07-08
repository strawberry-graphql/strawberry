from contextlib import contextmanager
from typing import Any, Dict, List

from graphql import MiddlewareManager

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

    def _run_on_all_extensions(self, method_name: str, *args, **kwargs):
        for extension in self.extensions:
            getattr(extension, method_name)(*args, **kwargs)

    @contextmanager
    def request(self):
        self._run_on_all_extensions("on_request_start")

        yield

        self._run_on_all_extensions("on_request_end")

    @contextmanager
    def validation(self):
        self._run_on_all_extensions("on_validation_start")

        yield

        self._run_on_all_extensions("on_validation_end")

    @contextmanager
    def parsing(self):
        self._run_on_all_extensions("on_parsing_start")

        yield

        self._run_on_all_extensions("on_parsing_end")

    def get_extensions_results(self) -> Dict[str, Any]:
        data = {}

        for extension in self.extensions:
            data.update(extension.get_results())

        return data

    def as_middleware_manager(self, *additional_middlewares) -> MiddlewareManager:
        middlewares = tuple(self.extensions) + additional_middlewares

        return MiddlewareManager(*middlewares)
