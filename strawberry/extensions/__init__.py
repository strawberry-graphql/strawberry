import functools
import typing
from contextlib import contextmanager

from graphql import MiddlewareManager


class Extension:
    def on_request_start(self):
        ...

    def on_request_end(self):
        ...

    def on_validation_start(self):
        ...

    def on_validation_end(self):
        ...

    def on_parsing_start(self):
        ...

    def on_parsing_end(self):
        ...

    def on_resolver_start(self):
        ...

    def on_resolver_end(self):
        ...

    def resolve(self, _next, root, info, *args, **kwargs):
        ...

    def get_results(self):
        return {}


def run_on_all_extension(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        method_name_start = f"on_{func.__name__}_start"
        method_name_end = f"on_{func.__name__}_end"

        for extension in self.extensions:
            getattr(extension, method_name_start)()

        result = func(self, *args, **kwargs)

        for extension in self.extensions:
            getattr(extension, method_name_end)()

        return result

    return wrap


class ExtensionsRunner:
    def __init__(self, extensions: typing.List[Extension] = None):
        self.extensions = extensions or []

    @contextmanager
    @run_on_all_extension
    def request(self):
        yield

    @contextmanager
    @run_on_all_extension
    def validation(self):

        yield

    @contextmanager
    @run_on_all_extension
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
