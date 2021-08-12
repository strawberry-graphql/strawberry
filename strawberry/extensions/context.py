from abc import ABC
from typing import TYPE_CHECKING, Awaitable

from strawberry.extensions.constants import (
    ON_PARSING_END,
    ON_PARSING_START,
    ON_REQUEST_END,
    ON_REQUEST_START,
    ON_VALIDATION_END,
    ON_VALIDATION_START,
)


if TYPE_CHECKING:
    from strawberry.extensions.runner import ExtensionsRunner


class ExtensionContextManager(ABC):
    enter_method: str
    exit_method: str

    def __init__(self, runner: "ExtensionsRunner"):
        self.runner = runner

    def __enter__(self) -> None:
        return self.runner.run_on_all_extensions(self.enter_method)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return self.runner.run_on_all_extensions(self.exit_method)

    def __aenter__(self) -> Awaitable[None]:
        return self.runner.run_on_all_extensions_async(self.enter_method)

    def __aexit__(self, exc_type, exc_val, exc_tb) -> Awaitable[None]:
        return self.runner.run_on_all_extensions_async(self.exit_method)


class RequestContextManager(ExtensionContextManager):
    enter_method = ON_REQUEST_START
    exit_method = ON_REQUEST_END


class ValidationContextManager(ExtensionContextManager):
    enter_method = ON_VALIDATION_START
    exit_method = ON_VALIDATION_END


class ParsingContextManager(ExtensionContextManager):
    enter_method = ON_PARSING_START
    exit_method = ON_PARSING_END
