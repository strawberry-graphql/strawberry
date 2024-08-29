from __future__ import annotations

import asyncio
import dataclasses
import inspect
from collections import defaultdict
from collections.abc import AsyncIterable
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    ForwardRef,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)
from typing_extensions import Annotated, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.field_extension import (
    AsyncExtensionResolver,
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.relay.exceptions import (
    RelayWrongAnnotationError,
    RelayWrongResolverAnnotationError,
)
from strawberry.types.arguments import StrawberryArgument, argument
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.field import _RESOLVER_TYPE, StrawberryField, field
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.lazy_type import LazyType
from strawberry.utils.aio import asyncgen_to_list
from strawberry.utils.typing import eval_type, is_generic_alias

from .types import Connection, GlobalID, Node, NodeIterableType, NodeType

if TYPE_CHECKING:
    from typing_extensions import Literal

    from strawberry.permission import BasePermission
    from strawberry.types.info import Info


class NodeExtension(FieldExtension):
    def apply(self, field: StrawberryField) -> None:
        assert field.base_resolver is None

        if isinstance(field.type, StrawberryList):
            resolver = self.get_node_list_resolver(field)
        else:
            resolver = self.get_node_resolver(field)  # type: ignore

        field.base_resolver = StrawberryResolver(resolver, type_override=field.type)

    def resolve(
        self, next_: SyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:
        return next_(source, info, **kwargs)

    async def resolve_async(
        self, next_: SyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:
        retval = next_(source, info, **kwargs)
        # If the resolve_nodes method is not async, retval will not actually
        # be awaitable. We still need the `resolve_async` in here because
        # otherwise this extension can't be used together with other
        # async extensions.
        return await retval if inspect.isawaitable(retval) else retval

    def get_node_resolver(
        self, field: StrawberryField
    ) -> Callable[[Info, GlobalID], Union[Node, None, Awaitable[Union[Node, None]]]]:
        type_ = field.type
        is_optional = isinstance(type_, StrawberryOptional)

        def resolver(
            info: Info,
            id: Annotated[GlobalID, argument(description="The ID of the object.")],
        ) -> Union[Node, None, Awaitable[Union[Node, None]]]:
            return id.resolve_type(info).resolve_node(
                id.node_id,
                info=info,
                required=not is_optional,
            )

        return resolver

    def get_node_list_resolver(
        self, field: StrawberryField
    ) -> Callable[[Info, List[GlobalID]], Union[List[Node], Awaitable[List[Node]]]]:
        type_ = field.type
        assert isinstance(type_, StrawberryList)
        is_optional = isinstance(type_.of_type, StrawberryOptional)

        def resolver(
            info: Info,
            ids: Annotated[
                List[GlobalID], argument(description="The IDs of the objects.")
            ],
        ) -> Union[List[Node], Awaitable[List[Node]]]:
            nodes_map: DefaultDict[Type[Node], List[str]] = defaultdict(list)
            # Store the index of the node in the list of nodes of the same type
            # so that we can return them in the same order while also supporting
            # different types
            index_map: Dict[GlobalID, Tuple[Type[Node], int]] = {}
            for gid in ids:
                node_t = gid.resolve_type(info)
                nodes_map[node_t].append(gid.node_id)
                index_map[gid] = (node_t, len(nodes_map[node_t]) - 1)

            resolved_nodes = {
                node_t: node_t.resolve_nodes(
                    info=info,
                    node_ids=node_ids,
                    required=not is_optional,
                )
                for node_t, node_ids in nodes_map.items()
            }
            awaitable_nodes = {
                node_t: nodes
                for node_t, nodes in resolved_nodes.items()
                if inspect.isawaitable(nodes)
            }
            # Async generators are not awaitable, so we need to handle them separately
            asyncgen_nodes = {
                node_t: nodes
                for node_t, nodes in resolved_nodes.items()
                if inspect.isasyncgen(nodes)
            }

            if awaitable_nodes or asyncgen_nodes:

                async def resolve(resolved: Any = resolved_nodes) -> List[Node]:
                    resolved.update(
                        zip(
                            [
                                *awaitable_nodes.keys(),
                                *asyncgen_nodes.keys(),
                            ],
                            # Resolve all awaitable nodes concurrently
                            await asyncio.gather(
                                *awaitable_nodes.values(),
                                *(
                                    asyncgen_to_list(nodes)  # type: ignore
                                    for nodes in asyncgen_nodes.values()
                                ),
                            ),
                        )
                    )

                    # Resolve any generator to lists
                    resolved = {
                        node_t: list(nodes) for node_t, nodes in resolved.items()
                    }
                    return [
                        resolved[index_map[gid][0]][index_map[gid][1]] for gid in ids
                    ]

                return resolve()

            # Resolve any generator to lists
            resolved = {
                node_t: list(cast(Iterator[Node], nodes))
                for node_t, nodes in resolved_nodes.items()
            }
            return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in ids]

        return resolver


class ConnectionExtension(FieldExtension):
    connection_type: Type[Connection[Node]]

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
            raise RelayWrongAnnotationError(field.name, cast(type, field.origin))

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
            raise RelayWrongResolverAnnotationError(field.name, field.base_resolver)

        self.connection_type = cast(Type[Connection[Node]], field.type)

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
            cast(Iterable[Node], next_(source, info, **kwargs)),
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
            cast(Iterable[Node], nodes),
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


if TYPE_CHECKING:
    node = field
else:

    def node(*args: Any, **kwargs: Any) -> StrawberryField:
        kwargs["extensions"] = [*kwargs.get("extensions", []), NodeExtension()]
        return field(*args, **kwargs)


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
    """Annotate a property or a method to create a relay connection field.

    Relay connections are mostly used for pagination purposes. This decorator
    helps creating a complete relay endpoint that provides default arguments
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
        some_node: relay.Connection[SomeType] = relay.connection(
            resolver=get_some_nodes,
            description="ABC",
        )

        @relay.connection(relay.Connection[SomeType], description="ABC")
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

    .. _Relay connections:
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


__all__ = ["node", "connection"]
