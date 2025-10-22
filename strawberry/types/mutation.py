from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    overload,
)

from strawberry.types.field import (
    _RESOLVER_TYPE,
    _RESOLVER_TYPE_ASYNC,
    _RESOLVER_TYPE_SYNC,
    StrawberryField,
    T,
    field,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Literal

    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.permission import BasePermission

# NOTE: we are separating the sync and async resolvers because using both
# in the same function will cause mypy to raise an error. Not sure if it is a bug


@overload
def mutation(
    *,
    resolver: _RESOLVER_TYPE_ASYNC[T],
    name: str | None = None,
    description: str | None = None,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def mutation(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: str | None = None,
    description: str | None = None,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def mutation(
    *,
    name: str | None = None,
    description: str | None = None,
    init: Literal[True] = True,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> Any: ...


@overload
def mutation(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


@overload
def mutation(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


def mutation(
    resolver: _RESOLVER_TYPE[Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False] | None = None,
) -> Any:
    """Annotates a method or property as a GraphQL mutation.

    Args:
        resolver: The resolver for the field. It can be a sync or async function.
        name: The GraphQL name of the field.
        description: The GraphQL description of the field.
        permission_classes: The permission classes required to access the field.
        deprecation_reason: The deprecation reason for the field.
        default: The default value for the field.
        default_factory: The default factory for the field.
        metadata: The metadata for the field.
        directives: The directives for the field.
        extensions: The extensions for the field.
        graphql_type: The GraphQL type for the field, useful when you want to use a
            different type in the resolver than the one in the schema.
        init: This parameter is used by PyRight to determine whether this field is
            added in the constructor or not. It is not used to change any behavior at
            the moment.

    Returns:
        The field object.

    This is normally used inside a type declaration:

    ```python
    import strawberry


    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, title: str, content: str) -> Post: ...
    ```

    It can be used both as decorator and as a normal function.
    """
    return field(
        resolver=resolver,  # type: ignore
        name=name,
        description=description,
        permission_classes=permission_classes,
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives,
        extensions=extensions,
        graphql_type=graphql_type,
    )


# NOTE: we are separating the sync and async resolvers because using both
# in the same function will cause mypy to raise an error. Not sure if it is a bug


@overload
def subscription(
    *,
    resolver: _RESOLVER_TYPE_ASYNC[T],
    name: str | None = None,
    description: str | None = None,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def subscription(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: str | None = None,
    description: str | None = None,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def subscription(
    *,
    name: str | None = None,
    description: str | None = None,
    init: Literal[True] = True,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> Any: ...


@overload
def subscription(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


@overload
def subscription(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


def subscription(
    resolver: _RESOLVER_TYPE[Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    init: Literal[True, False] | None = None,
) -> Any:
    """Annotates a method or property as a GraphQL subscription.

    Args:
        resolver: The resolver for the field.
        name: The GraphQL name of the field.
        description: The GraphQL description of the field.
        permission_classes: The permission classes required to access the field.
        deprecation_reason: The deprecation reason for the field.
        default: The default value for the field.
        default_factory: The default factory for the field.
        metadata: The metadata for the field.
        directives: The directives for the field.
        extensions: The extensions for the field.
        graphql_type: The GraphQL type for the field, useful when you want to use a
            different type in the resolver than the one in the schema.
        init: This parameter is used by PyRight to determine whether this field is
            added in the constructor or not. It is not used to change any behavior at
            the moment.

    Returns:
        The field for the subscription.

    This is normally used inside a type declaration:

    ```python
    import strawberry


    @strawberry.type
    class Subscription:
        @strawberry.subscription
        def post_created(self, title: str, content: str) -> Post: ...
    ```

    it can be used both as decorator and as a normal function.
    """
    return field(
        resolver=resolver,  # type: ignore
        name=name,
        description=description,
        is_subscription=True,
        permission_classes=permission_classes,
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives,
        extensions=extensions,
        graphql_type=graphql_type,
    )


__all__ = ["mutation", "subscription"]
