import asyncio
import dataclasses
import inspect
import sys
from collections import defaultdict
from typing import (  # type: ignore[attr-defined]
    Any,
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    ForwardRef,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    _eval_type,
    cast,
    overload,
)
from typing_extensions import Literal, Self, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.field import _RESOLVER_TYPE, StrawberryField
from strawberry.lazy_type import LazyType
from strawberry.permission import BasePermission
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.info import Info
from strawberry.types.types import TypeDefinition
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.cached_property import cached_property

from .types import Connection, GlobalID, Node, NodeType


class RelayField(StrawberryField):
    """Base relay field, containing utilities for both Node and Connection fields."""

    default_args: Dict[str, StrawberryArgument]

    def __init__(self, *args, **kwargs):
        default_args = getattr(self.__class__, "default_args", {})
        if isinstance(default_args, dict):
            self.default_args = default_args.copy()
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
            self.default_args.update(
                {
                    "ids": StrawberryArgument(
                        python_name="ids",
                        graphql_name=None,
                        type_annotation=StrawberryAnnotation(List[GlobalID]),
                        description="The IDs of the objects.",
                    ),
                }
            )
        elif not self.base_resolver:
            self.default_args.update(
                {
                    "id": StrawberryArgument(
                        python_name="id",
                        graphql_name=None,
                        type_annotation=StrawberryAnnotation(GlobalID),
                        description="The ID of the object.",
                    ),
                }
            )

    def __call__(self, resolver):
        raise TypeError("NodeField cannot have a resolver, use a common field instead.")

    def get_result(
        self,
        source: Any,
        info: Optional[Info],
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[Any], Any]:
        assert info is not None
        if self.is_list:
            return self.resolve_nodes(source, info, args, kwargs)
        else:
            return self.resolve_node(source, info, args, kwargs)

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
        gids: list[GlobalID] = kwargs["ids"]

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

        if any(inspect.isawaitable(v) for k, v in resolved_nodes.items()):

            async def resolve(resolved=resolved_nodes):
                resolved.update(
                    zip(
                        awaitable_nodes.keys(),
                        # Resolve all awaitable nodes concurrently
                        await asyncio.gather(*awaitable_nodes.values()),
                    )
                )
                # Resolve any generator to lists
                resolved = {node_t: list(nodes) for node_t, nodes in resolved.items()}
                return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in gids]

            return resolve()

        # Resolve any generator to lists
        resolved = {
            node_t: list(cast(Iterable[Node], nodes))
            for node_t, nodes in resolved_nodes.items()
        }
        return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in gids]


class ConnectionField(RelayField):
    """Relay Connection field.

    Do not instantiate this directly. Instead, use `@relay.connection`

    """

    default_args: Dict[str, StrawberryArgument] = {
        "before": StrawberryArgument(
            python_name="before",
            graphql_name=None,
            type_annotation=StrawberryAnnotation(Optional[str]),
            description=(
                "Returns the items in the list that come before the specified cursor."
            ),
            default=None,
        ),
        "after": StrawberryArgument(
            python_name="after",
            graphql_name=None,
            type_annotation=StrawberryAnnotation(Optional[str]),
            description=(
                "Returns the items in the list that come after the specified cursor."
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
                "Returns the items in the list that come after the specified cursor."
            ),
            default=None,
        ),
    }

    def __call__(self, resolver: _RESOLVER_TYPE):
        nodes_type = resolver.__annotations__.get("return")
        if nodes_type is not None:
            namespace = sys.modules[resolver.__module__].__dict__
            if isinstance(nodes_type, str):
                nodes_type = ForwardRef(nodes_type, is_argument=False)

            resolved = _eval_type(nodes_type, namespace, None)
            origin = get_origin(resolved)

            is_connection = (
                origin and isinstance(origin, type) and issubclass(origin, Connection)
            )
            is_iterable = (
                origin and isinstance(origin, type) and issubclass(origin, Iterable)
            )
            if not is_connection and not is_iterable:
                raise TypeError(
                    "Connection nodes resolver needs to return either a "
                    "`Connection[<NodeType]` or an Iterable like "
                    "`Iterable[<NodeType>]`, `List[<NodeType>]`, etc"
                )

            if is_iterable and not is_connection and self.type_annotation is None:
                ntype = get_args(resolved)[0]
                if isinstance(ntype, LazyType):
                    ntype = ntype.resolve_type()

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

            async def resolver():
                return self.resolver(
                    source,
                    info,
                    args,
                    kwargs,
                    nodes=await cast(Awaitable, nodes),
                )

            return resolver()

        # Avoid info being passed twice in case the custom resolver has one
        kwargs.pop("info", None)
        return self.resolve_connection(cast(Iterable[Node], nodes), info, **kwargs)

    def resolve_connection(
        self,
        nodes: Iterable[Node],
        info: Info,
        **kwargs,
    ):
        return_type = cast(Connection[Node], info.return_type)
        return return_type.from_nodes(nodes, **kwargs)


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
    )


@overload
def connection(
    *,
    resolver: _RESOLVER_TYPE[Union[Connection[NodeType], Iterable[NodeType]]],
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
) -> Any:
    ...


@overload
def connection(
    resolver: _RESOLVER_TYPE[Union[Connection[NodeType], Iterable[NodeType]]],
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
    graphql_type: Optional[Any] = None,
    # This init parameter is used by pyright to determine whether this field
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
    )
    if resolver is not None:
        f = f(resolver)
    return f
