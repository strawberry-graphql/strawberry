from abc import ABC
from typing import List

from strawberry.extensions import Extension
from strawberry.utils.await_maybe import await_maybe


class ExtensionContextManager(ABC):
    enter_method: str
    exit_method: str

    def __init__(self, extensions: List[Extension]):
        self.extensions = extensions


class RequestContextManager(ExtensionContextManager):
    def __enter__(self):
        for extension in self.extensions:
            extension.on_request_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            extension.on_request_end()

    async def __aenter__(self):
        for extension in self.extensions:
            await await_maybe(extension.on_request_start())

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            await await_maybe(extension.on_request_end())


class ValidationContextManager(ExtensionContextManager):
    def __enter__(self):
        for extension in self.extensions:
            extension.on_validation_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            extension.on_validation_end()

    async def __aenter__(self):
        for extension in self.extensions:
            await await_maybe(extension.on_validation_start())

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            await await_maybe(extension.on_validation_end())


class ParsingContextManager(ExtensionContextManager):
    def __enter__(self):
        for extension in self.extensions:
            extension.on_parsing_start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            extension.on_parsing_end()

    async def __aenter__(self):
        for extension in self.extensions:
            await await_maybe(extension.on_parsing_start())

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for extension in self.extensions:
            await await_maybe(extension.on_parsing_end())
