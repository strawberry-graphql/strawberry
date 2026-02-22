import sys
from collections.abc import Callable, Iterable

from strawberry.types.scalar import ScalarDefinition, identity


def scalar(
    *,
    name: str,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
) -> ScalarDefinition:
    """Creates a GraphQL custom scalar definition with federation support.

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
        authenticated: Whether to add the @authenticated directive.
        inaccessible: Whether to add the @inaccessible directive.
        policy: The list of policy names to add to the @policy directive.
        requires_scopes: The list of scopes to add to the @requires directive.
        tags: The list of tags to add to the @tag directive.

    Returns:
        A `ScalarDefinition`.

    Example usage:

    ```python
    from typing import NewType
    import strawberry
    from strawberry.schema.config import StrawberryConfig

    # Define the type
    Base64 = NewType("Base64", bytes)

    # Configure the scalar with federation directives
    schema = strawberry.federation.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                Base64: strawberry.federation.scalar(
                    name="Base64",
                    serialize=lambda v: base64.b64encode(v).decode(),
                    parse_value=lambda v: base64.b64decode(v),
                    authenticated=True,
                )
            }
        ),
    )
    ```
    """
    from strawberry.federation.schema_directives import (
        Authenticated,
        Inaccessible,
        Policy,
        RequiresScopes,
        Tag,
    )

    all_directives = list(directives)

    if authenticated:
        all_directives.append(Authenticated())

    if inaccessible:
        all_directives.append(Inaccessible())

    if policy:
        all_directives.append(Policy(policies=policy))

    if requires_scopes:
        all_directives.append(RequiresScopes(scopes=requires_scopes))

    if tags:
        all_directives.extend(Tag(name=tag) for tag in tags)

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
        directives=tuple(all_directives),
        origin=None,
        _source_file=_source_file,
        _source_line=_source_line,
    )


__all__ = ["scalar"]
