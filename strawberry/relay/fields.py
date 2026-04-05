from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    cast,
)

from strawberry.extensions.field_extension import (
    FieldExtension,
    SyncExtensionResolver,
)
from strawberry.pagination.fields import ConnectionExtension, connection
from strawberry.types.arguments import argument
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.cast import cast as strawberry_cast
from strawberry.types.field import StrawberryField, field
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.unset import UNSET
from strawberry.utils.aio import asyncgen_to_list

from .types import GlobalID, Node  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import (
        Awaitable,
        Callable,
        Iterable,
    )

    import strawberry


class NodeExtension(FieldExtension):
    def apply(self, field: StrawberryField) -> None:
        assert field.base_resolver is None

        if isinstance(field.type, StrawberryList):
            resolver = self.get_node_list_resolver(field)
        else:
            resolver = self.get_node_resolver(field)  # type: ignore

        field.base_resolver = StrawberryResolver(resolver, type_override=field.type)

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        retval = next_(source, info, **kwargs)
        # If the resolve_nodes method is not async, retval will not actually
        # be awaitable. We still need the `resolve_async` in here because
        # otherwise this extension can't be used together with other
        # async extensions.
        return await retval if inspect.isawaitable(retval) else retval

    def get_node_resolver(
        self, field: StrawberryField
    ) -> Callable[[strawberry.Info, GlobalID], Node | None | Awaitable[Node | None]]:
        type_ = field.type
        is_optional = isinstance(type_, StrawberryOptional)

        def resolver(
            info: strawberry.Info,
            id: Annotated[GlobalID, argument(description="The ID of the object.")],
        ) -> Node | None | Awaitable[Node | None]:
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

            return cast("Node", strawberry_cast(node_type, resolved_node))

        return resolver

    def get_node_list_resolver(
        self, field: StrawberryField
    ) -> Callable[
        [strawberry.Info, list[GlobalID]], list[Node] | Awaitable[list[Node]]
    ]:
        type_ = field.type
        assert isinstance(type_, StrawberryList)
        is_optional = isinstance(type_.of_type, StrawberryOptional)

        def resolver(
            info: strawberry.Info,
            ids: Annotated[
                list[GlobalID], argument(description="The IDs of the objects.")
            ],
        ) -> list[Node] | Awaitable[list[Node]]:
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
                return [cast("Node", strawberry_cast(node_t, node)) for node in nodes]

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
                            strict=True,
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
                node_t: cast_nodes(node_t, cast("Iterable[Node]", nodes))
                for node_t, nodes in resolved_nodes.items()
            }
            return [resolved[index_map[gid][0]][index_map[gid][1]] for gid in ids]

        return resolver


if TYPE_CHECKING:
    node = field
else:

    def node(*args: Any, default: Any = UNSET, **kwargs: Any) -> StrawberryField:
        kwargs["extensions"] = [*kwargs.get("extensions", []), NodeExtension()]
        # The default value is a stub for dataclasses so you can instantiate
        # types with relay.node() fields without explicit initialization.
        # The actual value is resolved by the NodeExtension resolver.
        return field(*args, default=default, **kwargs)


__all__ = ["ConnectionExtension", "NodeExtension", "connection", "node"]
