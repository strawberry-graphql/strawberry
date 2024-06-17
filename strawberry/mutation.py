from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    overload,
)
from typing_extensions import Annotated, Doc, Literal

from .field import (
    _RESOLVER_TYPE,
    _RESOLVER_TYPE_ASYNC,
    _RESOLVER_TYPE_SYNC,
    StrawberryField,
    T,
    field,
)

if TYPE_CHECKING:
    from typing_extensions import Literal

    from strawberry.extensions.field_extension import FieldExtension

    from .permission import BasePermission

# NOTE: we are separating the sync and async resolvers because using both
# in the same function will cause mypy to raise an error. Not sure if it is a bug


@overload
def mutation(
    *,
    resolver: _RESOLVER_TYPE_ASYNC[T],
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def mutation(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def mutation(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> Any: ...


@overload
def mutation(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


@overload
def mutation(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


def mutation(
    resolver: Annotated[
        Optional[_RESOLVER_TYPE[Any]], Doc("Resolver for the field")
    ] = None,
    *,
    name: Annotated[Optional[str], Doc("The GraphQL name of the field")] = None,
    description: Annotated[
        Optional[str], Doc("The GraphQL description of the field")
    ] = None,
    permission_classes: Annotated[
        Optional[List[Type[BasePermission]]],
        Doc("The permission classes required to access the field"),
    ] = None,
    deprecation_reason: Annotated[
        Optional[str], Doc("The deprecation reason for the field")
    ] = None,
    default: Annotated[
        Any, Doc("The default value for the field")
    ] = dataclasses.MISSING,
    default_factory: Annotated[
        Union[Callable[..., object], object], Doc("The default factory for the field")
    ] = dataclasses.MISSING,
    metadata: Annotated[
        Optional[Mapping[Any, Any]], Doc("The metadata for the field")
    ] = None,
    directives: Annotated[
        Optional[Sequence[object]], Doc("The directives for the field")
    ] = (),
    extensions: Annotated[
        Optional[List[FieldExtension]], Doc("The extensions for the field")
    ] = None,
    graphql_type: Annotated[
        Optional[Any],
        Doc(
            "The GraphQL type for the field, useful when you want to use a different type in the resolver than the one in the schema"
        ),
    ] = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotates a method or property as a GraphQL mutation.

    This is normally used inside a type declaration:

    ```python
    import strawberry


    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, title: str, content: str) -> Post: ...
    ```

    it can be used both as decorator and as a normal function.
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
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def subscription(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def subscription(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> Any: ...


@overload
def subscription(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


@overload
def subscription(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


def subscription(
    resolver: Annotated[
        Optional[_RESOLVER_TYPE[Any]], Doc("Resolver for the field")
    ] = None,
    *,
    name: Annotated[Optional[str], Doc("The GraphQL name of the field")] = None,
    description: Annotated[
        Optional[str], Doc("The GraphQL description of the field")
    ] = None,
    permission_classes: Annotated[
        Optional[List[Type[BasePermission]]],
        Doc("The permission classes required to access the field"),
    ] = None,
    deprecation_reason: Annotated[
        Optional[str], Doc("The deprecation reason for the field")
    ] = None,
    default: Annotated[
        Any, Doc("The default value for the field")
    ] = dataclasses.MISSING,
    default_factory: Annotated[
        Union[Callable[..., object], object], Doc("The default factory for the field")
    ] = dataclasses.MISSING,
    metadata: Annotated[
        Optional[Mapping[Any, Any]], Doc("The metadata for the field")
    ] = None,
    directives: Annotated[
        Optional[Sequence[object]], Doc("The directives for the field")
    ] = (),
    extensions: Annotated[
        Optional[List[FieldExtension]], Doc("The extensions for the field")
    ] = None,
    graphql_type: Annotated[
        Optional[Any],
        Doc(
            "The GraphQL type for the field, useful when you want to use a different type in the resolver than the one in the schema"
        ),
    ] = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotates a method or property as a GraphQL subscription.

    This is normally used inside a type declaration:

    ```python
    import strawberry


    @strawberry.type
    class Mutation:
        @strawberry.subscription
        def create_post(self, title: str, content: str) -> Post: ...
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
