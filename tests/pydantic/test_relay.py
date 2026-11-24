import re
from collections.abc import Iterable

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry import relay
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.pydantic.exceptions import StrawberryBaseBeforeModelError
from strawberry.relay.exceptions import NodeIDAnnotationError

FRUITS = {1: "Strawberry", 2: "Banana"}


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
    ) -> list["Fruit | None"]:
        return [
            Fruit(id=int(node_id), name=FRUITS[int(node_id)])
            if int(node_id) in FRUITS
            else None
            for node_id in node_ids
        ]


@strawberry.type
class Query:
    node: relay.Node = relay.node()
    nodes: list[relay.Node | None] = relay.node()

    @relay.connection(relay.ListConnection[Fruit])
    def fruits(self) -> list[Fruit]:
        return [Fruit(id=id_, name=name) for id_, name in FRUITS.items()]


# `relay.node()` fields can only be part of one schema
schema = strawberry.Schema(query=Query, types=[Fruit])


def test_types_can_implement_relay_node():
    sdl = str(schema)
    start = sdl.index("type Fruit ")

    assert sdl[start : sdl.index("}", start) + 1] == snapshot("""\
type Fruit implements Node {
  name: String!

  \"""The Globally Unique ID of this object\"""
  id: ID!
}\
""")
    # the `NodeID` field is part of the model, but not of the schema
    assert list(Fruit.model_fields) == ["id", "name"]

    result = schema.execute_sync("{ fruits { edges { node { id name } } } }")

    assert not result.errors
    assert result.data == {
        "fruits": {
            "edges": [
                {"node": {"id": relay.to_base64("Fruit", 1), "name": "Strawberry"}},
                {"node": {"id": relay.to_base64("Fruit", 2), "name": "Banana"}},
            ]
        }
    }


def test_nodes_are_resolved_by_their_global_id():
    result = schema.execute_sync(
        "query ($id: ID!, $ids: [ID!]!) { "
        "node(id: $id) { id ... on Fruit { name } } "
        "nodes(ids: $ids) { ... on Fruit { name } } }",
        variable_values={
            "id": relay.to_base64("Fruit", 2),
            "ids": [relay.to_base64("Fruit", 1), relay.to_base64("Fruit", 3)],
        },
    )

    assert not result.errors
    assert result.data == {
        "node": {"id": relay.to_base64("Fruit", 2), "name": "Banana"},
        "nodes": [{"name": "Strawberry"}, None],
    }


async def test_nodes_can_be_resolved_asynchronously():
    @strawberry.pydantic.type
    class Seed(pydantic.BaseModel, relay.Node):
        code: relay.NodeID[str]

        @classmethod
        async def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list["Seed"]:
            return [Seed(code=node_id) for node_id in node_ids]

    @strawberry.type
    class Query:
        node: relay.Node = relay.node()

    schema = strawberry.Schema(query=Query, types=[Seed])

    result = await schema.execute(
        "query ($id: ID!) { node(id: $id) { ... on Seed { id } } }",
        variable_values={"id": relay.to_base64("Seed", "abc")},
    )

    assert not result.errors
    assert result.data == {"node": {"id": relay.to_base64("Seed", "abc")}}


def test_types_can_resolve_their_own_id():
    @strawberry.pydantic.type
    class Tag(pydantic.BaseModel, relay.Node):
        slug: str

        @classmethod
        def resolve_id(cls, root: "Tag", *, info: strawberry.Info) -> str:
            return root.slug.upper()

    @strawberry.type
    class Query:
        @strawberry.field
        def tag(self) -> Tag:
            return Tag(slug="jam")

    result = strawberry.Schema(query=Query).execute_sync("{ tag { id slug } }")

    assert not result.errors
    assert result.data == {"tag": {"id": relay.to_base64("Tag", "JAM"), "slug": "jam"}}


def test_types_can_override_the_id_field_of_relay_node():
    # like with `@strawberry.type`, the type's own `id` field replaces the one
    # of `relay.Node`
    @strawberry.pydantic.type
    class Fruit(pydantic.BaseModel, relay.Node):
        code: relay.NodeID[int]

        @strawberry.pydantic.field
        def id(self) -> relay.GlobalID:
            return relay.GlobalID("Fruit", f"custom-{self.code}")

    @strawberry.type
    class Query:
        @strawberry.field
        def fruit(self) -> Fruit:
            return Fruit(code=1)

    result = strawberry.Schema(query=Query).execute_sync("{ fruit { id } }")

    assert not result.errors
    assert result.data == {"fruit": {"id": relay.to_base64("Fruit", "custom-1")}}


def test_interfaces_can_implement_relay_node():
    @strawberry.pydantic.interface
    class Entity(pydantic.BaseModel, relay.Node):
        id: relay.NodeID[int]

    @strawberry.pydantic.type
    class Seller(Entity):
        shop: str

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list["Seller"]:
            return [Seller(id=int(node_id), shop="Jam & co") for node_id in node_ids]

    @strawberry.type
    class Query:
        node: relay.Node = relay.node()

    schema = strawberry.Schema(query=Query, types=[Seller])

    assert "type Seller implements Entity & Node {" in str(schema)

    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { id ... on Seller { shop } } }",
        variable_values={"id": relay.to_base64("Seller", 7)},
    )

    assert not result.errors
    assert result.data == {
        "node": {"id": relay.to_base64("Seller", 7), "shop": "Jam & co"}
    }


@pytest.mark.raises_strawberry_exception(
    NodeIDAnnotationError,
    match=re.escape('No field annotated with `NodeID` found in "Fruit"') + "$",
)
def test_types_implementing_relay_node_need_a_node_id():
    @strawberry.pydantic.type
    class Fruit(pydantic.BaseModel, relay.Node):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def fruit(self) -> Fruit:
            return Fruit(name="Strawberry")

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    StrawberryBaseBeforeModelError,
    match=re.escape(
        "Pydantic type `Fruit` extends the Strawberry interface `Node` before a "
        "Pydantic model"
    )
    + "$",
)
def test_relay_node_before_the_model_raises_an_error():
    @strawberry.pydantic.type
    class Fruit(relay.Node, pydantic.BaseModel):
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
