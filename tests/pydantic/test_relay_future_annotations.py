from __future__ import annotations

from collections.abc import Iterable

import pydantic

import strawberry
from strawberry import relay


@strawberry.pydantic.type
class Fruit(pydantic.BaseModel, relay.Node):
    id: relay.NodeID[int]
    name: str

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Fruit]:
        return [Fruit(id=int(node_id), name="Strawberry") for node_id in node_ids]


def test_relay_node_with_postponed_annotations():
    # `relay.NodeID[int]` is a string here, which `relay.Node` resolves in the
    # module of the model
    @strawberry.type
    class Query:
        node: relay.Node = relay.node()

    schema = strawberry.Schema(query=Query, types=[Fruit])

    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { id ... on Fruit { name } } }",
        variable_values={"id": relay.to_base64("Fruit", 1)},
    )

    assert not result.errors
    assert result.data == {
        "node": {"id": relay.to_base64("Fruit", 1), "name": "Strawberry"}
    }
