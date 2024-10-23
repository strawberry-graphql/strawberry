from __future__ import annotations

import itertools
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterable,
    AsyncIterator,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Self, TypeAlias

from strawberry.types.base import (
    StrawberryContainer,
    get_object_definition,
)
from strawberry.types.field import field
from strawberry.types.info import Info  # noqa: TCH001
from strawberry.types.object_type import type
from strawberry.utils.aio import aenumerate, aislice
from strawberry.utils.inspect import in_async_context

from .utils import (
    SliceMetadata,
    should_resolve_list_connection_edges,
    to_base64,
)

if TYPE_CHECKING:
    from strawberry.utils.await_maybe import AwaitableOrValue

NodeType = TypeVar("NodeType")
NodeIterableType: TypeAlias = Union[
    Iterator[NodeType],
    Iterable[NodeType],
    AsyncIterator[NodeType],
    AsyncIterable[NodeType],
]

PREFIX = "arrayconnection"


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

    cursor: str = field(description="A cursor for use in pagination")
    node: NodeType = field(description="The item at the end of the edge")

    @classmethod
    def resolve_edge(cls, node: NodeType, *, cursor: Any = None) -> Self:
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

    page_info: PageInfo = field(description="Pagination data for this connection")
    edges: List[Edge[NodeType]] = field(
        description="Contains the nodes in this connection"
    )

    @classmethod
    def resolve_node(cls, node: Any, *, info: Info, **kwargs: Any) -> NodeType:
        """The identity function for the node.

        This method is used to resolve a node of a different type to the
        connection's `NodeType`.

        By default it returns the node itself, but subclasses can override
        this to provide a custom implementation.

        Args:
            node:
                The resolved node which should return an instance of this
                connection's `NodeType`.
            info:
                The strawberry execution info resolve the type name from.
            **kwargs:
                Additional arguments passed to the resolver.

        """
        return node

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Self]:
        """Resolve a connection from nodes.

        Subclasses must define this method to paginate nodes based
        on `first`/`last`/`before`/`after` arguments.

        Args:
            info: The strawberry execution info resolve the type name from.
            nodes: An iterable/iteretor of nodes to paginate.
            before: Returns the items in the list that come before the specified cursor.
            after: Returns the items in the list that come after the specified cursor.
            first: Returns the first n items from the list.
            last: Returns the items in the list that come after the specified cursor.
            kwargs: Additional arguments passed to the resolver.

        Returns:
            The resolved `Connection`

        """
        raise NotImplementedError


@type(name="Connection", description="A connection to a list of items.")
class ListConnection(Connection[NodeType]):
    """A connection to a list of items.

    Attributes:
        page_info:
            Pagination data for this connection
        edges:
            Contains the nodes in this connection

    """

    page_info: PageInfo = field(description="Pagination data for this connection")
    edges: List[Edge[NodeType]] = field(
        description="Contains the nodes in this connection"
    )

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Self]:
        """Resolve a connection from the list of nodes.

        This uses the described Connection Pagination algorithm_

        Args:
            info: The strawberry execution info resolve the type name from.
            nodes: An iterable/iteretor of nodes to paginate.
            before: Returns the items in the list that come before the specified cursor.
            after: Returns the items in the list that come after the specified cursor.
            first: Returns the first n items from the list.
            last: Returns the items in the list that come after the specified cursor.
            kwargs: Additional arguments passed to the resolver.

        Returns:
            The resolved `Connection`

        .. _Connection Pagination algorithm:
            https://relay.dev/graphql/connections.htm#sec-Pagination-algorithm
        """
        slice_metadata = SliceMetadata.from_arguments(
            info,
            before=before,
            after=after,
            first=first,
            last=last,
        )

        type_def = get_object_definition(cls)
        assert type_def
        field_def = type_def.get_field("edges")
        assert field_def

        field = field_def.resolve_type(type_definition=type_def)
        while isinstance(field, StrawberryContainer):
            field = field.of_type

        edge_class = cast(Edge[NodeType], field)

        if isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context():

            async def resolver() -> Self:
                try:
                    iterator = cast(
                        Union[AsyncIterator[NodeType], AsyncIterable[NodeType]],
                        cast(Sequence, nodes)[
                            slice_metadata.start : slice_metadata.overfetch
                        ],
                    )
                except TypeError:
                    # TODO: Why mypy isn't narrowing this based on the if above?
                    assert isinstance(nodes, (AsyncIterator, AsyncIterable))
                    iterator = aislice(
                        nodes,
                        slice_metadata.start,
                        slice_metadata.overfetch,
                    )

                # The slice above might return an object that now is not async
                # iterable anymore (e.g. an already cached django queryset)
                if isinstance(iterator, (AsyncIterator, AsyncIterable)):
                    edges: List[Edge] = [
                        edge_class.resolve_edge(
                            cls.resolve_node(v, info=info, **kwargs),
                            cursor=slice_metadata.start + i,
                        )
                        async for i, v in aenumerate(iterator)
                    ]
                else:
                    edges: List[Edge] = [  # type: ignore[no-redef]
                        edge_class.resolve_edge(
                            cls.resolve_node(v, info=info, **kwargs),
                            cursor=slice_metadata.start + i,
                        )
                        for i, v in enumerate(iterator)
                    ]

                has_previous_page = slice_metadata.start > 0
                if (
                    slice_metadata.expected is not None
                    and len(edges) == slice_metadata.expected + 1
                ):
                    # Remove the overfetched result
                    edges = edges[:-1]
                    has_next_page = True
                elif slice_metadata.end == sys.maxsize:
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
                cast(Sequence, nodes)[slice_metadata.start : slice_metadata.overfetch],
            )
        except TypeError:
            assert isinstance(nodes, (Iterable, Iterator))
            iterator = itertools.islice(
                nodes,
                slice_metadata.start,
                slice_metadata.overfetch,
            )

        if not should_resolve_list_connection_edges(info):
            return cls(
                edges=[],
                page_info=PageInfo(
                    start_cursor=None,
                    end_cursor=None,
                    has_previous_page=False,
                    has_next_page=False,
                ),
            )

        edges = [
            edge_class.resolve_edge(
                cls.resolve_node(v, info=info, **kwargs),
                cursor=slice_metadata.start + i,
            )
            for i, v in enumerate(iterator)
        ]

        has_previous_page = slice_metadata.start > 0
        if (
            slice_metadata.expected is not None
            and len(edges) == slice_metadata.expected + 1
        ):
            # Remove the overfetched result
            edges = edges[:-1]
            has_next_page = True
        elif slice_metadata.end == sys.maxsize:
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


__all__ = [
    "NodeIterableType",
    "NodeType",
    "PREFIX",
    "Connection",
    "Edge",
    "PageInfo",
    "ListConnection",
]
