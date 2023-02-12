import dataclasses
import inspect
import itertools
import sys
import uuid
from collections.abc import AsyncIterable, AsyncIterator, Iterator
from typing import (
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from typing_extensions import Annotated, Literal, Self, TypeAlias, get_args, get_origin

from strawberry.field import field
from strawberry.lazy_type import LazyType
from strawberry.object_type import interface, type
from strawberry.private import StrawberryPrivate
from strawberry.scalars import ID
from strawberry.type import StrawberryContainer
from strawberry.types.info import Info
from strawberry.types.types import TypeDefinition
from strawberry.utils.aio import aenumerate, aislice
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.inspect import in_async_context

from .utils import from_base64, to_base64

_T = TypeVar("_T")
_R = TypeVar("_R")
PREFIX = "arrayconnection"

NodeType = TypeVar("NodeType", bound="Node")


class GlobalIDValueError(ValueError):
    """GlobalID value error, usually related to parsing or serialization."""


@dataclasses.dataclass(order=True, frozen=True)
class GlobalID:
    """Global ID for relay types.

    Different from `strawberry.ID`, this ID wraps the original object ID in a string
    that contains both its GraphQL type name and the ID itself, and encodes it
    to a base64_ string.

    This object contains helpers to work with that, including method to retrieve
    the python object type or even the encoded node itself.

    Attributes:
        type_name:
            The type name part of the id
        node_id:
            The node id part of the id

    .. _base64:
        https://en.wikipedia.org/wiki/Base64

    """

    _nodes_cache: ClassVar[Dict[Tuple[int, str], Type["Node"]]] = {}

    type_name: str
    node_id: str

    def __post_init__(self):
        if not isinstance(self.type_name, str):
            raise GlobalIDValueError(
                f"type_name is expected to be a string, found {repr(self.type_name)}"
            )
        if not isinstance(self.node_id, str):
            raise GlobalIDValueError(
                f"node_id is expected to be a string, found {repr(self.node_id)}"
            )

    def __str__(self):
        return to_base64(self.type_name, self.node_id)

    @classmethod
    def from_id(cls, value: Union[str, ID]):
        """Create a new GlobalID from parsing the given value.

        Args:
            value:
                The value to be parsed, as a base64 string in the
                "TypeName:NodeID" format

        Returns:
            An instance of GLobalID

        Raises:
            GlobalIDValueError:
                If the value is not in a GLobalID format

        """
        try:
            type_name, node_id = from_base64(value)
        except ValueError as e:
            raise GlobalIDValueError(str(e)) from e

        return cls(type_name=type_name, node_id=node_id)

    def resolve_type(self, info: Info) -> Type["Node"]:
        """Resolve the internal type name to its type itself.

        Args:
            info:
                The strawberry execution info resolve the type name from

        Returns:
            The resolved GraphQL type for the execution info

        """
        schema = info.schema
        # Put the schema in the key so that different schemas can have different types
        key = (id(schema), self.type_name)
        origin = self._nodes_cache.get(key)

        if origin is None:
            type_def = info.schema.get_type_by_name(self.type_name)
            assert isinstance(type_def, TypeDefinition)
            origin = (
                type_def.origin.resolve_type
                if isinstance(origin, LazyType)
                else type_def.origin
            )
            assert issubclass(origin, Node)
            self._nodes_cache[key] = origin

        return origin

    @overload
    def resolve_node(
        self,
        info: Info,
        *,
        required: Literal[True] = ...,
        ensure_type: Type[_T],
    ) -> _T:
        ...

    @overload
    def resolve_node(
        self,
        info: Info,
        *,
        required: Literal[True],
        ensure_type: None = ...,
    ) -> "Node":
        ...

    @overload
    def resolve_node(
        self,
        info: Info,
        *,
        required: bool = ...,
        ensure_type: None = ...,
    ) -> Optional["Node"]:
        ...

    def resolve_node(self, info, *, required=False, ensure_type=None) -> Any:
        """Resolve the type name and node id info to the node itself.

        Tip: When you know the expected type, calling `ensure_type` should help
        not only to enforce it, but also help with typing since it will know that,
        if this function returns successfully, the retval should be of that
        type and not `Node`.

        Args:
            info:
                The strawberry execution info resolve the type name from
            required:
                If the value is required to exist. Note that asking to ensure
                the type automatically makes required true.
            ensure_type:
                Optionally check if the returned node is really an instance
                of this type.

        Returns:
            The resolved node

        Raises:
            TypeError:
                If ensure_type was provided and the type is not an instance of it

        """
        n_type = self.resolve_type(info)
        node = n_type.resolve_node(
            self.node_id,
            info=info,
            required=required or ensure_type is not None,
        )

        if node is not None and ensure_type is not None:
            origin = get_origin(ensure_type)
            if origin and origin is Union:
                ensure_type = tuple(get_args(ensure_type))

            if not isinstance(node, ensure_type):
                raise TypeError(f"{ensure_type} expected, found {repr(node)}")

        return node

    @overload
    async def aresolve_node(
        self,
        info: Info,
        *,
        required: Literal[True] = ...,
        ensure_type: Type[_T],
    ) -> _T:
        ...

    @overload
    async def aresolve_node(
        self,
        info: Info,
        *,
        required: Literal[True],
        ensure_type: None = ...,
    ) -> "Node":
        ...

    @overload
    async def aresolve_node(
        self,
        info: Info,
        *,
        required: bool = ...,
        ensure_type: None = ...,
    ) -> Optional["Node"]:
        ...

    async def aresolve_node(self, info, *, required=False, ensure_type=None) -> Any:
        """Resolve the type name and node id info to the node itself.

        Tip: When you know the expected type, calling `ensure_type` should help
        not only to enforce it, but also help with typing since it will know that,
        if this function returns successfully, the retval should be of that
        type and not `Node`.

        Args:
            info:
                The strawberry execution info resolve the type name from
            required:
                If the value is required to exist. Note that asking to ensure
                the type automatically makes required true.
            ensure_type:
                Optionally check if the returned node is really an instance
                of this type.

        Returns:
            The resolved node

        Raises:
            TypeError:
                If ensure_type was provided and the type is not an instance of it

        """
        n_type = self.resolve_type(info)
        node = cast(
            Awaitable[Node],
            n_type.resolve_node(
                self.node_id,
                info=info,
                required=required or ensure_type is not None,
            ),
        )

        res = await node if node is not None else None

        if ensure_type is not None:
            origin = get_origin(ensure_type)
            if origin and origin is Union:
                ensure_type = tuple(get_args(ensure_type))

            if not isinstance(res, ensure_type):
                raise TypeError(f"{ensure_type} expected, found {repr(res)}")

        return res


class NodeIDPrivate(StrawberryPrivate):
    ...


NodeID: TypeAlias = Annotated[_T, NodeIDPrivate()]


@interface(description="An object with a Globally Unique ID")
class Node:
    """Node interface for GraphQL types.

    Subclasses must type the id field using `NodeID`. It will be private to the
    schema because it will be converted to a global ID and exposed as `id: GlobalID!`

    The following methods can also be implemented:
        resolve_id:
            (Optional) Called to resolve the node's id. Can be overriden to
            customize how the id is retrieved (e.g. in case you don't want
            to define a `NodeID` field)
        resolve_nodes:
            Called to retrieve an iterable of node given their ids
        resolve_node:
            (Optional) Called to retrieve a node given its id. If not defined
            the default implementation will call `.resolve_nodes` with that
            single node id.

    Example:
        >>> @strawberry.type
        ... class Fruit(Node):
        ...     id: NodeID[int]
        ...     name: str
        ...
        ... @classmethod
        ... def resolve_nodes(cls, *, info, node_ids, required=False):
        ...     # Return an iterable of fruits in here
        ...     ...

    """

    _id_attr: ClassVar[str] = "id"

    def __init_subclass__(cls, **kwargs):
        annotations: Dict[str, Type] = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, "__annotations__", {}))

        candidates = [
            attr
            for attr, annotation in annotations.items()
            if (
                get_origin(annotation) is Annotated
                and any(
                    isinstance(argument, NodeIDPrivate)
                    for argument in get_args(annotation)
                )
            )
        ]
        if len(candidates) > 1:
            raise TypeError(
                f"More than one field annotated with `NodeID` found on {cls!r}"
            )
        elif len(candidates) == 1:
            cls._id_attr = candidates[0]

    @field(name="id", description="The Globally Unique ID of this object")
    @classmethod
    def _id(cls, root: "Node", info: Info) -> GlobalID:
        # FIXME: We want to support both integration objects that doesn't define
        # a resolve_id and also the ones that does override it. Is there a better
        # way of handling this?
        if isinstance(root, Node):
            resolve_id = root.__class__.resolve_id
        else:
            # Try to use a custom resolve_id from the type itself. If it doesn't
            # define one, fallback to cls.resolve_id
            try:
                parent_type = info._raw_info.parent_type
                type_def = info.schema.get_type_by_name(parent_type.name)
                if not isinstance(type_def, TypeDefinition):
                    raise RuntimeError

                resolve_id = type_def.origin.resolve_id
            except (RuntimeError, AttributeError):
                resolve_id = cls.resolve_id

        node_id = resolve_id(root, info=info)
        resolve_typename = (
            root.__class__.resolve_typename
            if isinstance(root, Node)
            else cls.resolve_typename
        )
        type_name = resolve_typename(root, info)
        assert type_name

        if isinstance(node_id, str):
            # str is the default and is faster to check for it than is_awaitable
            return GlobalID(type_name=type_name, node_id=node_id)
        elif isinstance(node_id, (int, uuid.UUID)):
            # those are very common ids and are safe to convert to str
            return GlobalID(type_name=type_name, node_id=str(node_id))
        elif inspect.isawaitable(node_id):

            async def resolve():
                return GlobalID(
                    type_name=type_name,
                    node_id=await cast(Awaitable, node_id),
                )

            return cast(GlobalID, resolve())

        # If node_id is not str, GlobalID will raise an error for us
        return GlobalID(type_name=type_name, node_id=cast(str, node_id))

    @classmethod
    def resolve_id(
        cls,
        root: Self,
        *,
        info: Info,
    ) -> AwaitableOrValue[str]:
        """Resolve the node id.

        By default this will return `getattr(root, <id_attr>)`, where <id_attr>
        is the field typed with `NodeID`.

        You can override this method to provide a custom implementation.

        Args:
            info:
                The strawberry execution info resolve the type name from
            root:
                The node to resolve

        Returns:
            The resolved id (which is expected to be str)

        """
        return getattr(root, cls._id_attr)

    @classmethod
    def resolve_typename(cls, root: Self, info: Info):
        return info.path.typename

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
    ) -> AwaitableOrValue[Iterable[Self]]:
        ...

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: Literal[True],
    ) -> AwaitableOrValue[Iterable[Self]]:
        ...

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Optional[Iterable[str]] = None,
        required: Literal[False] = ...,
    ) -> AwaitableOrValue[Iterable[Optional[Self]]]:
        ...

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Optional[Iterable[str]] = None,
        required: bool,
    ) -> Union[
        AwaitableOrValue[Iterable[Self]],
        AwaitableOrValue[Iterable[Optional[Self]]],
    ]:
        ...

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Optional[Iterable[str]] = None,
        required: bool = False,
    ):
        """Resolve a list of nodes.

        This method *should* be defined by anyone implementing the `Node` interface.

        Args:
            info:
                The strawberry execution info resolve the type name from
            node_ids:
                Optional list of ids that, when provided, should be used to filter
                the results to only contain the nodes of those ids. When empty,
                all nodes of this type shall be returned.
            required:
                If `True`, all `node_ids` requested must exist. If they don't,
                an error must be raised. If `False`, missing nodes should be
                returned as `None`. It only makes sense when passing a list of
                `node_ids`, otherwise it will should ignored.

        Returns:
            An iterable of resolved nodes.

        """
        raise NotImplementedError  # pragma: no cover

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: Literal[True],
    ) -> AwaitableOrValue[Self]:
        ...

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: Literal[False] = ...,
    ) -> AwaitableOrValue[Optional[Self]]:
        ...

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: bool,
    ) -> AwaitableOrValue[Optional[Self]]:
        ...

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: bool = False,
    ) -> AwaitableOrValue[Optional[Self]]:
        """Resolve a node given its id.

        This method is a convenience method that calls `resolve_nodes` for
        a single node id.

        Args:
            info:
                The strawberry execution info resolve the type name from
            node_id:
                The id of the node to be retrieved
            required:
                if the node is required or not to exist. If not, then None
                should be returned if it doesn't exist. Otherwise an exception
                should be raised.

        Returns:
            The resolved node or None if it was not found

        """
        retval = cls.resolve_nodes(info=info, node_ids=[node_id], required=required)
        if inspect.isawaitable(retval):

            async def resolver():
                return next(iter(await retval))  # type: ignore[misc]

            return resolver()

        return next(iter(cast(Iterable[Self], retval)))


@type(description="Information to aid in pagination.")
class PageInfo:
    """Information to aid in pagination.

    Attributes:
        has_next_page:
            When paginating forwards, are there more items?
        has_previous_page:
            When paginating backwards, are there more items?
        start_cursor:
            When paginating backwards, the cursor to continue
        end_cursor:
            When paginating forwards, the cursor to continue

    """

    has_next_page: bool = field(
        description="When paginating forwards, are there more items?",
    )
    has_previous_page: bool = field(
        description="When paginating backwards, are there more items?",
    )
    start_cursor: Optional[str] = field(
        description="When paginating backwards, the cursor to continue.",
    )
    end_cursor: Optional[str] = field(
        description="When paginating forwards, the cursor to continue.",
    )


@type(description="An edge in a connection.")
class Edge(Generic[NodeType]):
    """An edge in a connection.

    Attributes:
        cursor:
            A cursor for use in pagination
        node:
            The item at the end of the edge

    """

    cursor: str = field(
        description="A cursor for use in pagination",
    )
    node: NodeType = field(
        description="The item at the end of the edge",
    )

    @classmethod
    def from_node(cls, node: NodeType, *, cursor: Any = None):
        return cls(cursor=to_base64(PREFIX, cursor), node=node)


@type(description="A connection to a list of items.")
class Connection(Generic[NodeType]):
    """A connection to a list of items.

    Attributes:
        page_info:
            Pagination data for this connection
        edges:
            Contains the nodes in this connection

    """

    page_info: PageInfo = field(
        description="Pagination data for this connection",
    )
    edges: List[Edge[NodeType]] = field(
        description="Contains the nodes in this connection",
    )

    @overload
    @classmethod
    def from_nodes(
        cls,
        nodes: Union[
            Iterator[NodeType],
            AsyncIterator[NodeType],
            Iterable[NodeType],
            AsyncIterable[NodeType],
        ],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs,
    ) -> Self:
        ...

    @overload
    @classmethod
    def from_nodes(
        cls,
        nodes: Union[
            Iterator[_T],
            AsyncIterator[_T],
            Iterable[_T],
            AsyncIterable[_T],
        ],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        node_converter: Callable[[_T], NodeType],
        **kwargs,
    ) -> Self:
        ...

    @classmethod
    def from_nodes(
        cls,
        nodes: Union[
            Iterator[NodeType],
            AsyncIterator[NodeType],
            Iterable[NodeType],
            AsyncIterable[NodeType],
            Iterator[_T],
            AsyncIterator[_T],
            Iterable[_T],
            AsyncIterable[_T],
        ],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        node_converter: Optional[Callable[[_T], NodeType]] = None,
        **kwargs,
    ):
        """Resolve a connection from the list of nodes.

        This uses the described Relay Pagination algorithm_

        Args:
            info:
                The strawberry execution info resolve the type name from
            nodes:
                An iterable of nodes to transform to a connection
            before:
                Returns the items in the list that come before the specified cursor
            after:
                Returns the items in the list that come after the specified cursor
            first:
                Returns the first n items from the list
            last:
                Returns the items in the list that come after the specified cursor

        Returns:
            The resolved `Connection`

        .. _Relay Pagination algorithm:
            https://relay.dev/graphql/connections.htm#sec-Pagination-algorithm

        """
        max_results = info.schema.config.relay_max_results
        start = 0
        end: Optional[int] = None

        if after:
            after_type, after_parsed = from_base64(after)
            assert after_type == PREFIX
            start = int(after_parsed) + 1
        if before:
            before_type, before_parsed = from_base64(before)
            assert before_type == PREFIX
            end = int(before_parsed)

        if isinstance(first, int):
            if first < 0:
                raise ValueError("Argument 'first' must be a non-negative integer.")

            if first > max_results:
                raise ValueError(
                    f"Argument 'first' cannot be higher than {max_results}."
                )

            if end is not None:
                start = max(0, end - 1)

            end = start + first
        if isinstance(last, int):
            if last < 0:
                raise ValueError("Argument 'last' must be a non-negative integer.")

            if last > max_results:
                raise ValueError(
                    f"Argument 'last' cannot be higher than {max_results}."
                )

            if end is not None:
                start = max(start, end - last)
            else:
                end = sys.maxsize

        if end is None:
            end = max_results

        expected = end - start if end != sys.maxsize else None
        # Overfetch by 1 to check if we have a next result
        overfetch = end + 1 if end != sys.maxsize else end

        type_def = cast(TypeDefinition, cls._type_definition)  # type:ignore
        field_def = type_def.get_field("edges")
        assert field_def

        field = field_def.type
        while isinstance(field, StrawberryContainer):
            field = field.of_type

        edge_class = cast(Edge[NodeType], field)

        if isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context():

            async def resolver():
                try:
                    iterator = cast(
                        Union[AsyncIterator[NodeType], AsyncIterable[NodeType]],
                        cast(Sequence, nodes)[start:overfetch],
                    )
                except TypeError:
                    # FIXME: Why mypy isn't narrowing this based on the if above?
                    assert isinstance(nodes, (AsyncIterator, AsyncIterable))
                    iterator = aislice(
                        nodes,  # type: ignore[arg-type]
                        start,
                        overfetch,
                    )

                assert isinstance(iterator, (AsyncIterator, AsyncIterable))
                edges: List[Edge] = [
                    edge_class.from_node(
                        (
                            node_converter(cast(_T, v))
                            if node_converter is not None
                            else cast(NodeType, v)  # type: ignore[redundant-cast]
                        ),
                        cursor=start + i,
                    )
                    async for i, v in aenumerate(iterator)
                ]

                has_previous_page = start > 0
                if expected is not None and len(edges) == expected + 1:
                    # Remove the overfetched result
                    edges = edges[:-1]
                    has_next_page = True
                elif end == sys.maxsize:
                    # Last was asked without any after/before
                    assert last is not None
                    original_len = len(edges)
                    edges = edges[-last:]
                    has_next_page = False
                    has_previous_page = len(edges) != original_len
                else:
                    has_next_page = False

                return cls(
                    edges=edges,
                    page_info=PageInfo(
                        start_cursor=edges[0].cursor if edges else None,
                        end_cursor=edges[-1].cursor if edges else None,
                        has_previous_page=has_previous_page,
                        has_next_page=has_next_page,
                    ),
                )

            return resolver()

        try:
            iterator = cast(
                Union[Iterator[NodeType], Iterable[NodeType]],
                cast(Sequence, nodes)[start:overfetch],
            )
        except TypeError:
            assert isinstance(nodes, (Iterable, Iterator))
            iterator = itertools.islice(
                nodes,  # type: ignore[arg-type]
                start,
                overfetch,
            )

        edges = [
            edge_class.from_node(
                (
                    node_converter(cast(_T, v))
                    if node_converter is not None
                    else cast(NodeType, v)  # type: ignore[redundant-cast]
                ),
                cursor=start + i,
            )
            for i, v in enumerate(iterator)
        ]

        has_previous_page = start > 0
        if expected is not None and len(edges) == expected + 1:
            # Remove the overfetched result
            edges = edges[:-1]
            has_next_page = True
        elif end == sys.maxsize:
            # Last was asked without any after/before
            assert last is not None
            original_len = len(edges)
            edges = edges[-last:]
            has_next_page = False
            has_previous_page = len(edges) != original_len
        else:
            has_next_page = False

        return cls(
            edges=edges,
            page_info=PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_previous_page=has_previous_page,
                has_next_page=has_next_page,
            ),
        )
