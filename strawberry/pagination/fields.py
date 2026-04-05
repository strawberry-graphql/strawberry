from __future__ import annotations

import dataclasses
import inspect
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from typing import (
    TYPE_CHECKING,
    Any,
    ForwardRef,
    Optional,
    cast,
    get_args,
    get_origin,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.base import StrawberryOptional
from strawberry.types.field import _RESOLVER_TYPE, StrawberryField
from strawberry.types.lazy_type import LazyType
from strawberry.utils.typing import eval_type, is_generic_alias, is_optional, is_union

from .exceptions import (
    ConnectionWrongAnnotationError,
    ConnectionWrongResolverAnnotationError,
)
from .types import Connection

if TYPE_CHECKING:
    from typing import Literal

    import strawberry
    from strawberry.permission import BasePermission


class ConnectionExtension(FieldExtension):
    connection_type: type[Connection]

    def __init__(self, max_results: int | None = None) -> None:
        self.max_results = max_results

    def apply(self, field: StrawberryField) -> None:
        field.arguments = [
            *field.arguments,
            StrawberryArgument(
                python_name="before",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),  # noqa: UP045
                description=(
                    "Returns the items in the list that come before the "
                    "specified cursor."
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="after",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),  # noqa: UP045
                description=(
                    "Returns the items in the list that come after the "
                    "specified cursor."
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="first",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),  # noqa: UP045
                description="Returns the first n items from the list.",
                default=None,
            ),
            StrawberryArgument(
                python_name="last",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),  # noqa: UP045
                description=(
                    "Returns the items in the list that come after the "
                    "specified cursor."
                ),
                default=None,
            ),
        ]

        f_type = field.type

        if isinstance(f_type, LazyType):
            f_type = f_type.resolve_type()
            field.type = f_type

        if isinstance(f_type, StrawberryOptional):
            f_type = f_type.of_type

        if isinstance(f_type, LazyType):
            f_type = f_type.resolve_type()

        type_origin = get_origin(f_type) if is_generic_alias(f_type) else f_type
        if isinstance(type_origin, LazyType):
            type_origin = type_origin.resolve_type()

        if not isinstance(type_origin, type) or not issubclass(type_origin, Connection):
            raise ConnectionWrongAnnotationError(field.name, cast("type", field.origin))

        assert field.base_resolver
        # TODO: We are not using resolver_type.type because it will call
        # StrawberryAnnotation.resolve, which will strip async types from the
        # type (i.e. AsyncGenerator[Fruit] will become Fruit). This is done there
        # for subscription support, but we can't use it here. Maybe we can refactor
        # this in the future.
        resolver_type = field.base_resolver.signature.return_annotation
        if isinstance(resolver_type, str):
            resolver_type = ForwardRef(resolver_type)
        if isinstance(resolver_type, ForwardRef):
            resolver_type = eval_type(
                resolver_type,
                field.base_resolver._namespace,
                None,
            )

        if is_union(resolver_type):
            assert is_optional(resolver_type)

            resolver_type = get_args(resolver_type)[0]

        origin = get_origin(resolver_type)

        if origin is None or not issubclass(
            origin, (Iterator, Iterable, AsyncIterator, AsyncIterable)
        ):
            raise ConnectionWrongResolverAnnotationError(
                field.name, field.base_resolver
            )

        self.connection_type = cast("type[Connection]", f_type)

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        *,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        return self.connection_type.resolve_connection(
            cast("Iterable", next_(source, info, **kwargs)),
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=self.max_results,
        )

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        *,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        nodes = next_(source, info, **kwargs)
        # nodes might be an AsyncIterable/AsyncIterator
        # In this case we don't await for it
        if inspect.isawaitable(nodes):
            nodes = await nodes

        resolved = self.connection_type.resolve_connection(
            cast("Iterable", nodes),
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=self.max_results,
        )

        # If nodes was an AsyncIterable/AsyncIterator, resolve_connection
        # will return a coroutine which we need to await
        if inspect.isawaitable(resolved):
            resolved = await resolved
        return resolved


# we used to have `Type[Connection[NodeType]]` here, but that when we added
# support for making the Connection type optional, we had to change it to
# `Any` because otherwise it wouldn't be type check since `Optional[Connection[Something]]`
# is not a `Type`, but a special form, see https://discuss.python.org/t/is-annotated-compatible-with-type-t/43898/46
# for more information, and also https://peps.python.org/pep-0747/, which is currently
# in draft status (and no type checker supports it yet)
ConnectionGraphQLType = Any


def connection(
    graphql_type: ConnectionGraphQLType | None = None,
    *,
    resolver: _RESOLVER_TYPE[Any] | None = None,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    max_results: int | None = None,
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behaviour at the moment.
    init: Literal[True, False] | None = None,
) -> Any:
    """Annotate a property or a method to create a connection field.

    Connections are mostly used for pagination purposes. This decorator
    helps creating a complete connection endpoint that provides default arguments
    and has a default implementation for the connection slicing.

    Note that when setting a resolver to this field, it is expected for this
    resolver to return an iterable of the expected node type, not the connection
    itself. That iterable will then be paginated accordingly. So, the main use
    case for this is to provide a filtered iterable of nodes by using some custom
    filter arguments.

    Args:
        graphql_type: The type of the nodes in the connection. This is used to
            determine the type of the edges and the node field in the connection.
        resolver: The resolver for the connection. This is expected to return an
            iterable of the expected node type.
        name: The GraphQL name of the field.
        is_subscription: Whether the field is a subscription.
        description: The GraphQL description of the field.
        permission_classes: The permission classes to apply to the field.
        deprecation_reason: The deprecation reason of the field.
        default: The default value of the field.
        default_factory: The default factory of the field.
        metadata: The metadata of the field.
        directives: The directives to apply to the field.
        extensions: The extensions to apply to the field.
        max_results: The maximum number of results this connection can return.
            Can be set to override the default value of 100 defined in the
            schema configuration.
        init: Used only for type checking purposes.

    Examples:
    Annotating something like this:

    ```python
    @strawberry.type
    class X:
        some_node: Connection[SomeType] = connection(
            resolver=get_some_nodes,
            description="ABC",
        )

        @connection(Connection[SomeType], description="ABC")
        def get_some_nodes(self, age: int) -> Iterable[SomeType]: ...
    ```

    Will produce a query like this:

    ```graphql
    query {
        someNode (
            before: String
            after: String
            first: Int
            last: Int
            age: Int
        ) {
            totalCount
            pageInfo {
                hasNextPage
                hasPreviousPage
                startCursor
                endCursor
            }
            edges {
                cursor
                node {
                    id
                    ...
                }
            }
        }
    }
    ```

    .. _Connections:
        https://relay.dev/graphql/connections.htm

    """
    extensions = extensions or []
    f = StrawberryField(
        python_name=None,
        graphql_name=name,
        description=description,
        type_annotation=StrawberryAnnotation.from_annotation(graphql_type),
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives or (),
        extensions=[*extensions, ConnectionExtension(max_results=max_results)],
    )
    if resolver is not None:
        f = f(resolver)
    return f


__all__ = ["ConnectionExtension", "connection"]
