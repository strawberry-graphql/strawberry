import functools
import typing
from contextlib import contextmanager

from graphql import MiddlewareManager
from strawberry.types import ExecutionContext

from . import Extension


def run_on_all_extensions(func=None, pass_context=False):
    def decorator(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            method_name_start = f"on_{func.__name__}_start"
            method_name_end = f"on_{func.__name__}_end"

            extension_kwargs = (
                {"execution_context": self.execution_context} if pass_context else {}
            )

            for extension in self.extensions:
                getattr(extension, method_name_start)(**extension_kwargs)

            try:
                result = func(self, *args, **kwargs)

                return result

            finally:
                for extension in self.extensions:
                    getattr(extension, method_name_end)(**extension_kwargs)

        return wrap

    if func:
        return decorator(func)

    return decorator


class ExtensionsRunner:
    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: typing.Sequence[Extension] = None,
    ):
        self.execution_context = execution_context
        self.extensions = extensions or []

    @contextmanager
    @run_on_all_extensions(pass_context=True)
    def request(self):
        yield

    @contextmanager
    @run_on_all_extensions
    def validation(self):
        yield

    @contextmanager
    @run_on_all_extensions
    def parsing(self):
        yield

    def get_extensions_results(self) -> typing.Dict[str, typing.Any]:
        data = {}

        for extension in self.extensions:
            data.update(extension.get_results())

        return data

    def as_middleware_manager(self, *additional_middlewares) -> MiddlewareManager:
        middlewares = tuple(self.extensions) + additional_middlewares

        return MiddlewareManager(*middlewares)
