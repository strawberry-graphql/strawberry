from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
)

from strawberry.types.base import StrawberryType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from graphql import GraphQLScalarType


def identity(x: Any) -> Any:
    return x


@dataclass
class ScalarDefinition(StrawberryType):
    name: str
    description: str | None
    specified_by_url: str | None
    serialize: Callable | None
    parse_value: Callable | None
    parse_literal: Callable | None
    directives: Iterable[object] = ()
    origin: GraphQLScalarType | type | None = None

    # Optionally store the GraphQLScalarType instance so that we don't get
    # duplicates
    implementation: GraphQLScalarType | None = None

    # used for better error messages
    _source_file: str | None = None
    _source_line: int | None = None

    def copy_with(
        self, type_var_map: Mapping[str, StrawberryType | type]
    ) -> StrawberryType | type:
        return super().copy_with(type_var_map)  # type: ignore[safe-super]

    @property
    def is_graphql_generic(self) -> bool:
        return False


def scalar(
    *,
    name: str,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
) -> ScalarDefinition:
    """Creates a GraphQL custom scalar definition.

    Returns a `ScalarDefinition` for use in `StrawberryConfig.scalar_map`
    or `Schema(scalar_overrides=...)`.

    Args:
        name: The GraphQL name of the scalar.
        description: The description of the scalar.
        specified_by_url: The URL of the specification.
        serialize: The function to serialize the scalar.
        parse_value: The function to parse the value.
        parse_literal: The function to parse the literal.
        directives: The directives to apply to the scalar.

    Returns:
        A `ScalarDefinition`.

    Example usage:

    ```python
    from typing import NewType
    import strawberry
    from strawberry.schema.config import StrawberryConfig

    # Define the type
    Base64 = NewType("Base64", bytes)

    # Configure the scalar in schema config
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                Base64: strawberry.scalar(
                    name="Base64",
                    serialize=lambda v: base64.b64encode(v).decode(),
                    parse_value=lambda v: base64.b64decode(v),
                )
            }
        ),
    )
    ```
    """
    from strawberry.exceptions.handler import should_use_rich_exceptions

    _source_file = None
    _source_line = None

    if should_use_rich_exceptions():
        frame = sys._getframe(1)
        _source_file = frame.f_code.co_filename
        _source_line = frame.f_lineno

    return ScalarDefinition(
        name=name,
        description=description,
        specified_by_url=specified_by_url,
        serialize=serialize,
        parse_literal=parse_literal,
        parse_value=parse_value,
        directives=directives,
        origin=None,
        _source_file=_source_file,
        _source_line=_source_line,
    )


__all__ = ["ScalarDefinition", "identity", "scalar"]
