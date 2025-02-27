from __future__ import annotations

import asyncio
import dataclasses
import inspect
from collections import defaultdict
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ForwardRef,
    Optional,
    Union,
    cast,
)
from typing_extensions import get_args, get_origin

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
from strawberry.types.cast import cast as strawberry_cast
from strawberry.types.field import _RESOLVER_TYPE, StrawberryField, field
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.lazy_type import LazyType
from strawberry.utils.aio import asyncgen_to_list
from strawberry.utils.typing import eval_type, is_generic_alias, is_optional, is_union

from .types import Connection, GlobalID, Node

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
            node_type = id.resolve_type(info)
            resolved_node = node_type.resolve_node(
                id.node_id,
                info=info,
                required=not is_optional,
            )

            # We are using `strawberry_cast` here to cast the resolved node to make
            # sure `is_type_of` will not try to find its type again. Very important
            # when returning a non type (e.g. Django/SQLAlchemy/Pydantic model), as
            # we could end up resolving to a different type in case more than one
            # are registered.
            if inspect.isawaitable(resolved_node):

                async def resolve() -> Any:
                    return strawberry_cast(node_type, await resolved_node)

                return resolve()

            return cast(Node, strawberry_cast(node_type, resolved_node))

        return resolver

    def get_node_list_resolver(
        self, field: StrawberryField
    ) -> Callable[[Info, list[GlobalID]], Union[list[Node], Awaitable[list[Node]]]]:
        type_ = field.type
        assert isinstance(type_, StrawberryList)
        is_optional = isinstance(type_.of_type, StrawberryOptional)

        def resolver(
            info: Info,
            ids: Annotated[
                list[GlobalID], argument(description="The IDs of the objects.")
            ],
        ) -> Union[list[Node], Awaitable[list[Node]]]:
            nodes_map: defaultdict[type[Node], list[str]] = defaultdict(list)
            # Store the index of the node in the list of nodes of the same type
            # so that we can return them in the same order while also supporting
            # different types
            index_map: dict[GlobalID, tuple[type[Node], int]] = {}
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

            # We are using `strawberry_cast` here to cast the resolved node to make
            # sure `is_type_of` will not try to find its type again. Very important
            # when returning a non type (e.g. Django/SQLAlchemy/Pydantic model), as
            # we could end up resolving to a different type in case more than one
            # are registered
            def cast_nodes(node_t: type[Node], nodes: Iterable[Any]) -> list[Node]:
                return [cast(Node, strawberry_cast(node_t, node)) for node in nodes]

            if awaitable_nodes or asyncgen_nodes:

                async def resolve(resolved: Any = resolved_nodes) -> list[Node]:
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
                        node_t: cast_nodes(node_t, nodes)
                        for node_t, nodes in resolved.items()
                    }
                    return [
                        resolved[index_map[gid][0]][index_map[gid][1]] for gid in ids
                    ]

                return resolve()

            # Resolve any generator to lists
            resolved = {
                node_t: cast_nodes(node_t, cast(Iterable[Node], nodes))
                for node_t, nodes in resolved_nodes.items()
            }
            return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in ids]

        return resolver


class ConnectionExtension(FieldExtension):
    connection_type: type[Connection[Node]]

    def __init__(self, max_results: Optional[int] = None) -> None:
        self.max_results = max_results

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

        if isinstance(f_type, StrawberryOptional):
            f_type = f_type.of_type

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

        if is_union(resolver_type):
            assert is_optional(resolver_type)

            resolver_type = get_args(resolver_type)[0]

        origin = get_origin(resolver_type)

        if origin is None or not issubclass(
            origin, (Iterator, Iterable, AsyncIterator, AsyncIterable)
        ):
            raise RelayWrongResolverAnnotationError(field.name, field.base_resolver)

        self.connection_type = cast(type[Connection[Node]], f_type)

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
            max_results=self.max_results,
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
            max_results=self.max_results,
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


# we used to have `Type[Connection[NodeType]]` here, but that when we added
# support for making the Connection type optional, we had to change it to
# `Any` because otherwise it wouldn't be type check since `Optional[Connection[Something]]`
# is not a `Type`, but a special form, see https://discuss.python.org/t/is-annotated-compatible-with-type-t/43898/46
# for more information, and also https://peps.python.org/pep-0747/, which is currently
# in draft status (and no type checker supports it yet)
ConnectionGraphQLType = Any


def connection(
    graphql_type: Optional[ConnectionGraphQLType] = None,
    *,
    resolver: Optional[_RESOLVER_TYPE[Any]] = None,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[list[type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: list[FieldExtension] | None = None,
    max_results: Optional[int] = None,
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behaviour at the moment.
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
        max_results: The maximum number of results this connection can return.
            Can be set to override the default value of 100 defined in the
            schema configuration.
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


__all__ = ["connection", "node"]
