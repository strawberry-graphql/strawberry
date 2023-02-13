import asyncio
import dataclasses
import inspect
import sys
from collections import defaultdict
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from typing_extensions import Literal, Self, get_args, get_origin, get_type_hints

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions.missing_return_annotation import MissingReturnAnnotationError
from strawberry.field import _RESOLVER_TYPE, StrawberryField
from strawberry.lazy_type import LazyType
from strawberry.permission import BasePermission
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.info import Info
from strawberry.types.types import TypeDefinition
from strawberry.utils.aio import asyncgen_to_list, resolve_awaitable
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.cached_property import cached_property

from .exceptions import RelayWrongAnnotationError
from .types import Connection, GlobalID, Node, NodeIterableType, NodeType

_T = TypeVar("_T")


class RelayField(StrawberryField):
    """Base relay field, containing utilities for both Node and Connection fields."""

    default_args: Dict[str, StrawberryArgument]

    def __init__(
        self,
        *args,
        node_converter: Optional[Callable[[object], Node]] = None,
        **kwargs,
    ):
        self.node_converter = node_converter

        base_resolver = kwargs.pop("base_resolver", None)
        super().__init__(*args, **kwargs)
        if base_resolver:
            self.__call__(base_resolver)

    @property
    def arguments(self) -> List[StrawberryArgument]:
        args = {
            **self.default_args,
            **{arg.python_name: arg for arg in super().arguments},
        }
        return list(args.values())

    @cached_property
    def is_basic_field(self):
        return False

    @cached_property
    def is_optional(self):
        type_ = self.type
        if isinstance(type_, StrawberryList):
            type_ = type_.of_type

        return isinstance(type_, StrawberryOptional)

    @cached_property
    def is_list(self):
        type_ = self.type
        if isinstance(type_, StrawberryOptional):
            type_ = type_.of_type

        return isinstance(type_, StrawberryList)

    def copy_with(
        self,
        type_var_map: Mapping[TypeVar, Union[StrawberryType, type]],
    ) -> Self:
        retval = super().copy_with(type_var_map)
        retval.default_args = self.default_args
        return retval


class NodeField(RelayField):
    """Relay Node field.

    This field is used to fetch a single object by its ID or multiple
    objects given a list of IDs.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.base_resolver and self.is_list:
            self.default_args = {
                "ids": StrawberryArgument(
                    python_name="ids",
                    graphql_name=None,
                    type_annotation=StrawberryAnnotation(List[GlobalID]),
                    description="The IDs of the objects.",
                ),
            }
        elif not self.base_resolver:
            self.default_args = {
                "id": StrawberryArgument(
                    python_name="id",
                    graphql_name=None,
                    type_annotation=StrawberryAnnotation(GlobalID),
                    description="The ID of the object.",
                ),
            }

    def __call__(self, resolver):
        raise TypeError(
            "`NodeField` cannot have a resolver, use `@strawberry.field` instead."
        )

    def get_result(
        self,
        source: Any,
        info: Optional[Info],
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[Any], Any]:
        assert info is not None
        resolver = self.resolve_nodes if self.is_list else self.resolve_node

        return resolver(source, info, args, kwargs)

    def resolve_node(
        self,
        source: Any,
        info: Info,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> AwaitableOrValue[Optional[Node]]:
        gid = kwargs["id"]
        assert isinstance(gid, GlobalID)
        return gid.resolve_type(info).resolve_node(
            gid.node_id,
            info=info,
            required=not self.is_optional,
        )

    def resolve_nodes(
        self,
        source: Any,
        info: Info,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> AwaitableOrValue[List[Node]]:
        gids: List[GlobalID] = kwargs["ids"]

        nodes_map: DefaultDict[Type[Node], List[str]] = defaultdict(list)
        # Store the index of the node in the list of nodes of the same type
        # so that we can return them in the same order while also supporting different
        # types
        index_map: Dict[GlobalID, Tuple[Type[Node], int]] = {}
        for gid in gids:
            node_t = gid.resolve_type(info)
            nodes_map[node_t].append(gid.node_id)
            index_map[gid] = (node_t, len(nodes_map[node_t]) - 1)

        if len(nodes_map) == 0:
            return []

        resolved_nodes = {
            node_t: node_t.resolve_nodes(
                info=info,
                node_ids=node_ids,
                required=not self.is_optional,
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

            async def resolve(resolved=resolved_nodes):
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
                                asyncgen_to_list(nodes)
                                for nodes in asyncgen_nodes.values()
                            ),
                        ),
                    )
                )

                # Resolve any generator to lists
                resolved = {node_t: list(nodes) for node_t, nodes in resolved.items()}
                return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in gids]

            return resolve()

        # Resolve any generator to lists
        resolved = {
            node_t: list(cast(Iterator[Node], nodes))
            for node_t, nodes in resolved_nodes.items()
        }
        return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in gids]


class ConnectionField(RelayField):
    """Relay Connection field.

    Do not instantiate this directly. Instead, use `@relay.connection`

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.default_args = {
            "before": StrawberryArgument(
                python_name="before",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),
                description=(
                    "Returns the items in the list that come before the "
                    "specified cursor."
                ),
                default=None,
            ),
            "after": StrawberryArgument(
                python_name="after",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[str]),
                description=(
                    "Returns the items in the list that come after the "
                    "specified cursor."
                ),
                default=None,
            ),
            "first": StrawberryArgument(
                python_name="first",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
                description="Returns the first n items from the list.",
                default=None,
            ),
            "last": StrawberryArgument(
                python_name="last",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
                description=(
                    "Returns the items in the list that come after the "
                    "specified cursor."
                ),
                default=None,
            ),
        }

    def __call__(self, resolver: _RESOLVER_TYPE):
        namespace = sys.modules[resolver.__module__].__dict__
        resolved = get_type_hints(cast(Type, resolver), namespace).get("return")
        if resolved is None:
            raise MissingReturnAnnotationError(
                self.name, resolver=StrawberryResolver(resolver)
            )

        origin = get_origin(resolved)

        is_connection = (
            origin and isinstance(origin, type) and issubclass(origin, Connection)
        )
        is_iterable = (
            origin
            and isinstance(origin, type)
            and issubclass(origin, (Iterator, AsyncIterator, Iterable, AsyncIterable))
        )
        if not is_connection and not is_iterable:
            raise RelayWrongAnnotationError(
                field_name=self.name,
                resolver=StrawberryResolver(resolver),
            )

        if is_iterable and not is_connection and self.type_annotation is None:
            if self.node_converter is not None:
                ntype = get_type_hints(self.node_converter).get("return")
            else:
                ntype = get_args(resolved)[0]

            self.type_annotation = StrawberryAnnotation(
                Connection[ntype],  # type: ignore[valid-type]
                namespace=namespace,
            )

        return super().__call__(resolver)

    @cached_property
    def resolver_args(self) -> Set[str]:
        resolver = self.base_resolver
        if not resolver:
            return set()

        if isinstance(resolver, StrawberryResolver):
            resolver = resolver.wrapped_func  # type: ignore[assignment]

        return set(inspect.signature(cast(Callable, resolver)).parameters.keys())

    def get_result(
        self,
        source: Any,
        info: Optional[Info],
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[Any], Any]:
        assert info is not None
        type_def = info.return_type._type_definition  # type:ignore
        assert isinstance(type_def, TypeDefinition)

        field_type = type_def.type_var_map[cast(TypeVar, NodeType)]
        if isinstance(field_type, LazyType):
            field_type = field_type.resolve_type()

        if self.base_resolver is not None:
            # If base_resolver is not self.conn_resolver,
            # then it is defined to something
            assert self.base_resolver

            resolver_args = self.resolver_args
            resolver_kwargs = {
                # Consider both args not in default args and the ones specified
                # by the resolver, in case they want to check
                # "first"/"last"/"before"/"after"
                k: v
                for k, v in kwargs.items()
                if k in resolver_args
            }
            nodes = self.base_resolver(*args, **resolver_kwargs)
        else:
            nodes = None

        return self.resolver(source, info, args, kwargs, nodes=nodes)

    def resolver(
        self,
        source: Any,
        info: Info,
        args: List[Any],
        kwargs: Dict[str, Any],
        *,
        nodes: AwaitableOrValue[
            Optional[Union[Iterable[Node], Connection[Node]]]
        ] = None,
    ):
        # The base_resolver might have resolved to a Connection directly
        if isinstance(nodes, Connection):
            return nodes

        return_type = cast(Connection[Node], info.return_type)
        type_def = return_type._type_definition  # type:ignore
        assert isinstance(type_def, TypeDefinition)

        field_type = type_def.type_var_map[cast(TypeVar, NodeType)]
        if isinstance(field_type, LazyType):
            field_type = field_type.resolve_type()

        if nodes is None:
            nodes = cast(Node, field_type).resolve_nodes(info=info)

        if inspect.isawaitable(nodes):
            return resolve_awaitable(
                nodes,
                lambda resolved: self.resolver(
                    source,
                    info,
                    args,
                    kwargs,
                    nodes=resolved,
                ),
            )

        # Avoid info being passed twice in case the custom resolver has one
        kwargs.pop("info", None)
        return self.resolve_connection(cast(Iterable[Node], nodes), info, **kwargs)

    def resolve_connection(
        self,
        nodes: NodeIterableType[NodeType],
        info: Info,
        **kwargs,
    ):
        return_type = cast(Connection[Node], info.return_type)
        kwargs.setdefault("info", info)
        return return_type.from_nodes(
            nodes,
            node_converter=self.node_converter,
            **kwargs,
        )


def node(
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
    node_converter: Optional[Callable[[object], NodeType]] = None,
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotate a property to create a relay query field.

    Examples:
        Annotating something like this:

        >>> @strawberry.type
        >>> class X:
        ...     some_node: SomeType = relay.node(description="ABC")

        Will produce a query like this that returns `SomeType` given its id.

        ```
        query {
            someNode (id: ID) {
                id
                ...
            }
        }
        ```

    """
    return NodeField(
        python_name=None,
        graphql_name=name,
        type_annotation=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives or (),
        node_converter=node_converter,
    )


@overload
def connection(
    *,
    resolver: _RESOLVER_TYPE[NodeIterableType[NodeType]],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    graphql_type: Optional[Any] = None,
) -> Connection[NodeType]:
    ...


@overload
def connection(
    *,
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
    graphql_type: Optional[Any] = None,
    node_converter: Optional[Callable[[Any], NodeType]] = None,
) -> Any:
    ...


@overload
def connection(
    resolver: _RESOLVER_TYPE[NodeIterableType[NodeType]],
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
    graphql_type: Optional[Any] = None,
) -> ConnectionField:
    ...


@overload
def connection(
    resolver: _RESOLVER_TYPE[NodeIterableType[_T]],
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
    graphql_type: Optional[Any] = None,
    node_converter: Callable[[_T], NodeType],
) -> ConnectionField:
    ...


def connection(
    resolver: Optional[_RESOLVER_TYPE[Any]] = None,
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
    # This init parameter is used by pyright to determine whether this field
    graphql_type: Optional[Any] = None,
    node_converter: Optional[Callable[[Any], NodeType]] = None,
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotate a property or a method to create a relay connection field.

    Relay connections_ are mostly used for pagination purposes. This decorator
    helps creating a complete relay endpoint that provides default arguments
    and has a default implementation for the connection slicing.

    Note that when setting a resolver to this field, it is expected for this
    resolver to return an iterable of the expected node type, not the connection
    itself. That iterable will then be paginated accordingly. So, the main use
    case for this is to provide a filtered iterable of nodes by using some custom
    filter arguments.

    Examples:
        Annotating something like this:

        >>> @strawberry.type
        >>> class X:
        ...     some_node: relay.Connection[SomeType] = relay.connection(
        ...         description="ABC"
        ...     )
        ...
        ...     @relay.connection(description="ABC")
        ...     def get_some_nodes(self, age: int) -> Iterable[SomeType]:
        ...         ...

        Will produce a query like this:

        ```
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
    f = ConnectionField(
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
        node_converter=node_converter,
    )
    if resolver is not None:
        f = f(resolver)
    return f
