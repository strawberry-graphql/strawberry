from __future__ import annotations

import asyncio
import inspect
import warnings
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    Iterator,
    List,
    Tuple,
    Type,
    Union,
    cast,
)
from typing_extensions import Annotated

from strawberry.extensions.field_extension import (
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.pagination.fields import ConnectionExtension, connection
from strawberry.types.arguments import argument  # noqa: TCH001
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.field import StrawberryField, field
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.utils.aio import asyncgen_to_list

from .types import GlobalID, Node

if TYPE_CHECKING:
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


if TYPE_CHECKING:
    node = field
else:

    def node(*args: Any, **kwargs: Any) -> StrawberryField:
        kwargs["extensions"] = [*kwargs.get("extensions", []), NodeExtension()]
        return field(*args, **kwargs)


_DEPRECATIONS = {
    "ConnectionField": ConnectionExtension,
    "connection": connection,
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATIONS:
        warnings.warn(
            f"{name} should be imported from strawberry.pagination.fields",
            DeprecationWarning,
            stacklevel=2,
        )
        return _DEPRECATIONS[name]

    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["NodeExtension", "node"]
