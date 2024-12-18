from __future__ import annotations

import dataclasses
import inspect
from collections.abc import AsyncIterable
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    ForwardRef,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
    overload,
)
from typing_extensions import get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.field import _RESOLVER_TYPE, StrawberryField
from strawberry.types.lazy_type import LazyType
from strawberry.utils.typing import eval_type, is_generic_alias

from .exceptions import (
    ConnectionWrongAnnotationError,
    ConnectionWrongResolverAnnotationError,
)
from .types import Connection, NodeIterableType, NodeType

if TYPE_CHECKING:
    from typing_extensions import Literal

    from strawberry.permission import BasePermission
    from strawberry.types.info import Info


class ConnectionExtension(FieldExtension):
    connection_type: Type[Connection]

    def apply(self, field: StrawberryField) -> None:
        field.arguments = [
            *field.arguments,
            StrawberryArgument(
                python_name="before",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),
                description=(
                    "Returns the items in the list that come before the "
                    "specified cursor."
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="after",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),
                description=(
                    "Returns the items in the list that come after the "
                    "specified cursor."
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="first",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
                description="Returns the first n items from the list.",
                default=None,
            ),
            StrawberryArgument(
                python_name="last",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
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

        type_origin = get_origin(f_type) if is_generic_alias(f_type) else f_type
        if not isinstance(type_origin, type) or not issubclass(type_origin, Connection):
            raise ConnectionWrongAnnotationError(field.name, cast(type, field.origin))

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

        origin = get_origin(resolver_type)
        if origin is None or not issubclass(
            origin, (Iterator, Iterable, AsyncIterator, AsyncIterable)
        ):
            raise ConnectionWrongResolverAnnotationError(
                field.name, field.base_resolver
            )

        self.connection_type = cast(Type[Connection], field.type)

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        *,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        return self.connection_type.resolve_connection(
            cast(Iterable, next_(source, info, **kwargs)),
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
        )

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        *,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        nodes = next_(source, info, **kwargs)
        # nodes might be an AsyncIterable/AsyncIterator
        # In this case we don't await for it
        if inspect.isawaitable(nodes):
            nodes = await nodes

        resolved = self.connection_type.resolve_connection(
            cast(Iterable, nodes),
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
        )

        # If nodes was an AsyncIterable/AsyncIterator, resolve_connection
        # will return a coroutine which we need to await
        if inspect.isawaitable(resolved):
            resolved = await resolved
        return resolved


@overload
def connection(
    graphql_type: Optional[Type[Connection[NodeType]]] = None,
    *,
    resolver: Optional[_RESOLVER_TYPE[NodeIterableType[Any]]] = None,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: List[FieldExtension] = (),  # type: ignore
) -> Any: ...


@overload
def connection(
    graphql_type: Optional[Type[Connection[NodeType]]] = None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: List[FieldExtension] = (),  # type: ignore
) -> StrawberryField: ...


def connection(
    graphql_type: Optional[Type[Connection[NodeType]]] = None,
    *,
    resolver: Optional[_RESOLVER_TYPE[Any]] = None,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: List[FieldExtension] = (),  # type: ignore
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
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
            first: String
            after: String
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
        extensions=[*extensions, ConnectionExtension()],
    )
    if resolver is not None:
        f = f(resolver)
    return f


__all__ = ["ConnectionExtension", "connection"]
