import re
from collections.abc import Iterable

import pydantic
import pytest

import strawberry
from strawberry import relay
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.pydantic.exceptions import UnsupportedRelayNodeError


@pytest.mark.raises_strawberry_exception(
    UnsupportedRelayNodeError,
    match=re.escape(
        "`Fruit` implements `relay.Node`, which isn't supported by "
        "`strawberry.pydantic.type` yet"
    )
    + "$",
)
def test_types_cannot_implement_relay_node():
    @strawberry.pydantic.type
    class Fruit(pydantic.BaseModel, relay.Node):
        id: relay.NodeID[int]
        name: str


@pytest.mark.raises_strawberry_exception(
    UnsupportedRelayNodeError,
    match=re.escape(
        "`Fruit` implements `relay.Node`, which isn't supported by "
        "`strawberry.pydantic.type` yet"
    )
    + "$",
)
def test_types_with_their_own_id_field_cannot_implement_relay_node():
    # this would implement the interface, but `relay.Node` isn't supported yet
    @strawberry.pydantic.type
    class Fruit(pydantic.BaseModel, relay.Node):
        code: relay.NodeID[int]

        @strawberry.pydantic.field
        def id(self) -> relay.GlobalID:
            return relay.GlobalID("Fruit", str(self.code))


@pytest.mark.raises_strawberry_exception(
    UnsupportedRelayNodeError,
    match=re.escape(
        "`Entity` implements `relay.Node`, which isn't supported by "
        "`strawberry.pydantic.interface` yet"
    )
    + "$",
)
def test_interfaces_cannot_implement_relay_node():
    @strawberry.interface
    class Named(relay.Node):
        name: str

    @strawberry.pydantic.interface
    class Entity(Named, pydantic.BaseModel):
        id: relay.NodeID[int]


@pytest.mark.raises_strawberry_exception(
    InvalidSuperclassInterfaceError,
    match=re.escape("Input class 'FruitInput' cannot inherit from interface(s): Node")
    + "$",
)
def test_inputs_cannot_implement_relay_node():
    @strawberry.pydantic.input
    class FruitInput(pydantic.BaseModel, relay.Node):
        id: relay.NodeID[int]


def test_pydantic_types_can_be_the_nodes_of_connections():
    @strawberry.pydantic.type
    class Fruit(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> list[Fruit]:
            return [Fruit(name="Strawberry"), Fruit(name="Banana")]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ fruits(first: 1) { edges { node { name } } pageInfo { hasNextPage } } }"
    )

    assert not result.errors
    assert result.data == {
        "fruits": {
            "edges": [{"node": {"name": "Strawberry"}}],
            "pageInfo": {"hasNextPage": True},
        }
    }


def test_nodes_can_be_created_from_pydantic_models():
    @strawberry.pydantic.type
    class Origin(pydantic.BaseModel):
        country: str

    class FruitModel(pydantic.BaseModel):
        id: int
        name: str
        origin: Origin

    fruits = {1: FruitModel(id=1, name="Strawberry", origin=Origin(country="IT"))}

    @strawberry.type
    class Fruit(relay.Node):
        id: relay.NodeID[int]
        name: str
        origin: Origin

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list["Fruit"]:
            # `dict(model)` keeps the nested models, unlike `model_dump()`
            return [Fruit(**dict(fruits[int(node_id)])) for node_id in node_ids]

    @strawberry.type
    class Query:
        node: relay.Node = relay.node()

    schema = strawberry.Schema(query=Query, types=[Fruit])

    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { ... on Fruit { name origin { country } } } }",
        variable_values={"id": relay.to_base64("Fruit", 1)},
    )

    assert not result.errors
    assert result.data == {"node": {"name": "Strawberry", "origin": {"country": "IT"}}}
