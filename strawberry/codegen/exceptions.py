from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphql import GraphQLError


class CodegenError(Exception):
    pass


class NoOperationProvidedError(CodegenError):
    pass


class NoOperationNameProvidedError(CodegenError):
    pass


class MultipleOperationsProvidedError(CodegenError):
    pass


class InvalidOperationError(CodegenError):
    """The operation doesn't validate against the schema."""

    def __init__(self, errors: list[GraphQLError]) -> None:
        self.errors = errors
        self.messages = [_format_error(error) for error in errors]
        super().__init__("\n".join(self.messages))


def _format_error(error: GraphQLError) -> str:
    if not error.locations:
        return error.message

    location = error.locations[0]
    return f"{location.line}:{location.column}: {error.message}"


__all__ = [
    "CodegenError",
    "InvalidOperationError",
    "MultipleOperationsProvidedError",
    "NoOperationNameProvidedError",
    "NoOperationProvidedError",
]
