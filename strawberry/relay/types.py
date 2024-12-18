from __future__ import annotations

import dataclasses
import inspect
import sys
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    ClassVar,
    ForwardRef,
    Iterable,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from typing_extensions import Annotated, Literal, Self, TypeAlias, get_args, get_origin

from strawberry.pagination.types import (
    PREFIX,
    Connection,
    Edge,
    ListConnection,
    NodeIterableType,
    NodeType,
    PageInfo,
)
from strawberry.pagination.utils import (
    from_base64,
    to_base64,
)
from strawberry.relay.exceptions import NodeIDAnnotationError
from strawberry.types.base import (
    StrawberryObjectDefinition,
)
from strawberry.types.field import field
from strawberry.types.info import Info  # noqa: TCH001
from strawberry.types.lazy_type import LazyType
from strawberry.types.object_type import interface
from strawberry.types.private import StrawberryPrivate
from strawberry.utils.aio import resolve_awaitable
from strawberry.utils.typing import eval_type, is_classvar

if TYPE_CHECKING:
    from strawberry.scalars import ID
    from strawberry.utils.await_maybe import AwaitableOrValue

_T = TypeVar("_T")


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

    type_name: str
    node_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.type_name, str):
            raise GlobalIDValueError(
                f"type_name is expected to be a string, found {self.type_name!r}"
            )
        if not isinstance(self.node_id, str):
            raise GlobalIDValueError(
                f"node_id is expected to be a string, found {self.node_id!r}"
            )

    def __str__(self) -> str:
        return to_base64(self.type_name, self.node_id)

    @classmethod
    def from_id(cls, value: Union[str, ID]) -> Self:
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

    @overload
    async def resolve_node(
        self,
        info: Info,
        *,
        required: Literal[True] = ...,
        ensure_type: Type[_T],
    ) -> _T: ...

    @overload
    async def resolve_node(
        self,
        info: Info,
        *,
        required: Literal[True],
        ensure_type: None = ...,
    ) -> Node: ...

    @overload
    async def resolve_node(
        self,
        info: Info,
        *,
        required: bool = ...,
        ensure_type: None = ...,
    ) -> Optional[Node]: ...

    async def resolve_node(self, info, *, required=False, ensure_type=None) -> Any:
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
        node: Node | Awaitable[Node] = cast(
            Awaitable[Node],
            n_type.resolve_node(
                self.node_id,
                info=info,
                required=required or ensure_type is not None,
            ),
        )

        if node is not None and inspect.isawaitable(node):
            node = await node

        if ensure_type is not None:
            origin = get_origin(ensure_type)
            if origin and origin is Union:
                ensure_type = tuple(get_args(ensure_type))

            if not isinstance(node, ensure_type):
                msg = (
                    f"Cannot resolve. GlobalID requires {ensure_type}, received {node!r}. "
                    "Verify that the supplied ID is intended for this Query/Mutation/Subscription."
                )
                raise TypeError(msg)

        return node

    def resolve_type(self, info: Info) -> Type[Node]:
        """Resolve the internal type name to its type itself.

        Args:
            info:
                The strawberry execution info resolve the type name from

        Returns:
            The resolved GraphQL type for the execution info

        """
        type_def = info.schema.get_type_by_name(self.type_name)
        if not isinstance(type_def, StrawberryObjectDefinition):
            raise GlobalIDValueError(
                f"Cannot resolve. GlobalID requires a GraphQL type, "
                f"received `{self.type_name}`."
            )

        origin = (
            type_def.origin.resolve_type
            if isinstance(type_def.origin, LazyType)
            else type_def.origin
        )
        if not issubclass(origin, Node):
            raise GlobalIDValueError(
                f"Cannot resolve. GlobalID requires a GraphQL Node type, "
                f"received `{self.type_name}`."
            )
        return origin

    @overload
    def resolve_node_sync(
        self,
        info: Info,
        *,
        required: Literal[True] = ...,
        ensure_type: Type[_T],
    ) -> _T: ...

    @overload
    def resolve_node_sync(
        self,
        info: Info,
        *,
        required: Literal[True],
        ensure_type: None = ...,
    ) -> Node: ...

    @overload
    def resolve_node_sync(
        self,
        info: Info,
        *,
        required: bool = ...,
        ensure_type: None = ...,
    ) -> Optional[Node]: ...

    def resolve_node_sync(self, info, *, required=False, ensure_type=None) -> Any:
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
                msg = (
                    f"Cannot resolve. GlobalID requires {ensure_type}, received {node!r}. "
                    "Verify that the supplied ID is intended for this Query/Mutation/Subscription."
                )
                raise TypeError(msg)

        return node


class NodeIDPrivate(StrawberryPrivate):
    """Annotate a type attribute as its id.

    The `Node` interface will automatically create and resolve GlobalIDs
    based on the field annotated with `NodeID`. e.g:

    ```python
    import strawberry


    @strawberry.type
    class Fruit(Node):
        code: NodeID[str]
    ```

    In this case, `code` will be used to generate a global ID in the
    format `Fruit:<code>` and will be exposed as `id: GlobalID!` in the
    `Fruit` type.
    """


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
    ```python
    import strawberry


    @strawberry.type
    class Fruit(strawberry.relay.Node):
        id: strawberry.relay.NodeID[int]
        name: str

        @classmethod
        def resolve_nodes(cls, *, info, node_ids, required=False):
            # Return an iterable of fruits in here
            ...
    ```
    """

    _id_attr: ClassVar[Optional[str]] = None

    @field(name="id", description="The Globally Unique ID of this object")
    @classmethod
    def _id(cls, root: Node, info: Info) -> GlobalID:
        # NOTE: root might not be a Node instance when using integrations which
        # return an object that is compatible with the type (e.g. the django one).
        # In that case, we can retrieve the type itself from info
        if isinstance(root, Node):
            resolve_id = root.__class__.resolve_id
            resolve_typename = root.__class__.resolve_typename
        else:
            parent_type = info._raw_info.parent_type
            type_def = info.schema.get_type_by_name(parent_type.name)
            assert isinstance(type_def, StrawberryObjectDefinition)
            origin = cast(Type[Node], type_def.origin)
            resolve_id = origin.resolve_id
            resolve_typename = origin.resolve_typename

        type_name = resolve_typename(root, info)
        assert isinstance(type_name, str)
        node_id = resolve_id(root, info=info)
        assert node_id is not None

        if inspect.isawaitable(node_id):
            return cast(
                GlobalID,
                resolve_awaitable(
                    node_id,
                    lambda resolved: GlobalID(
                        type_name=type_name,
                        node_id=str(resolved),
                    ),
                ),
            )

        # If node_id is not str, GlobalID will raise an error for us
        return GlobalID(type_name=type_name, node_id=str(node_id))

    @classmethod
    def resolve_id_attr(cls) -> str:
        if cls._id_attr is not None:
            return cls._id_attr

        candidates: list[str] = []
        for base in cls.__mro__:
            base_namespace = sys.modules[base.__module__].__dict__

            for attr_name, attr in getattr(base, "__annotations__", {}).items():
                # Some ClassVar might raise TypeError when being resolved
                # on some python versions. This is fine to skip since
                # we are not interested in ClassVars here
                if is_classvar(base, attr):
                    continue

                evaled = eval_type(
                    ForwardRef(attr) if isinstance(attr, str) else attr,
                    globalns=base_namespace,
                )

                if get_origin(evaled) is Annotated and any(
                    isinstance(a, NodeIDPrivate) for a in get_args(evaled)
                ):
                    candidates.append(attr_name)

            # If we found candidates in this base, stop looking for more
            # This is to support subclasses to define something else than
            # its superclass as a NodeID
            if candidates:
                break

        if len(candidates) == 0:
            raise NodeIDAnnotationError(
                f'No field annotated with `NodeID` found in "{cls.__name__}"', cls
            )
        if len(candidates) > 1:
            raise NodeIDAnnotationError(
                (
                    "More than one field annotated with `NodeID` "
                    f'found in "{cls.__name__}"'
                ),
                cls,
            )

        cls._id_attr = candidates[0]
        return cls._id_attr

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
            info: The strawberry execution info resolve the type name from.
            root: The node to resolve.

        Returns:
            The resolved id (which is expected to be str)

        """
        return getattr(root, cls.resolve_id_attr())

    @classmethod
    def resolve_typename(cls, root: Self, info: Info) -> str:
        typename = info.path.typename
        assert typename is not None
        return typename

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: Literal[True],
    ) -> AwaitableOrValue[Iterable[Self]]: ...

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: Literal[False] = ...,
    ) -> AwaitableOrValue[Iterable[Optional[Self]]]: ...

    @overload
    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool,
    ) -> Union[
        AwaitableOrValue[Iterable[Self]],
        AwaitableOrValue[Iterable[Optional[Self]]],
    ]: ...

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ):
        """Resolve a list of nodes.

        This method *should* be defined by anyone implementing the `Node` interface.

        The nodes should be returned in the same order as the provided ids.
        Also, if `required` is `True`, all ids must be resolved or an error
        should be raised. If `required` is `False`, missing nodes should be
        returned as `None`.

        Args:
            info: The strawberry execution info resolve the type name from.
            node_ids: List of node ids that should be returned.
            required: If `True`, all `node_ids` requested must exist. If they don't,
                an error must be raised. If `False`, missing nodes should be
                returned as `None`. It only makes sense when passing a list of
                `node_ids`, otherwise it will should ignored.

        Returns:
            An iterable of resolved nodes.

        """
        raise NotImplementedError

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: Literal[True],
    ) -> AwaitableOrValue[Self]: ...

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: Literal[False] = ...,
    ) -> AwaitableOrValue[Optional[Self]]: ...

    @overload
    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Info,
        required: bool,
    ) -> AwaitableOrValue[Optional[Self]]: ...

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
            info: The strawberry execution info resolve the type name from.
            node_id: The id of the node to be retrieved.
            required: if the node is required or not to exist. If not, then None
                should be returned if it doesn't exist. Otherwise an exception
                should be raised.

        Returns:
            The resolved node or None if it was not found
        """
        retval = cls.resolve_nodes(info=info, node_ids=[node_id], required=required)

        if inspect.isawaitable(retval):
            return resolve_awaitable(retval, lambda resolved: next(iter(resolved)))

        return next(iter(cast(Iterable[Self], retval)))


_DEPRECATIONS = {
    "Connection": Connection,
    "Edge": Edge,
    "ListConnection": ListConnection,
    "NodeIterableType": NodeIterableType,
    "NodeType": NodeType,
    "PREFIX": PREFIX,
    "PageInfo": PageInfo,
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATIONS:
        warnings.warn(
            f"{name} should be imported from strawberry.pagination.types",
            DeprecationWarning,
            stacklevel=2,
        )
        return _DEPRECATIONS[name]

    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "GlobalID",
    "GlobalIDValueError",
    "Node",
    "NodeID",
    "NodeIDAnnotationError",
    "NodeIDPrivate",
]
