from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, Optional, Union, cast
from typing_extensions import assert_type
from unittest.mock import MagicMock

import pytest

import strawberry
from strawberry import relay
from strawberry.relay.utils import to_base64
from strawberry.types.info import Info

from .schema import Fruit, FruitAsync, fruits_resolver, schema


class FakeInfo:
    schema = schema


# We only need that info contains the schema for the tests
fake_info = cast(Info, FakeInfo())


@pytest.mark.parametrize("type_name", [None, 1, 1.1])
def test_global_id_wrong_type_name(type_name: Any):
    with pytest.raises(relay.GlobalIDValueError):
        relay.GlobalID(type_name=type_name, node_id="foobar")


@pytest.mark.parametrize("node_id", [None, 1, 1.1])
def test_global_id_wrong_type_node_id(node_id: Any):
    with pytest.raises(relay.GlobalIDValueError):
        relay.GlobalID(type_name="foobar", node_id=node_id)


def test_global_id_from_id():
    gid = relay.GlobalID.from_id("Zm9vYmFyOjE=")
    assert gid.type_name == "foobar"
    assert gid.node_id == "1"


@pytest.mark.parametrize("value", ["foobar", ["Zm9vYmFy"], 123])
def test_global_id_from_id_error(value: Any):
    with pytest.raises(relay.GlobalIDValueError):
        relay.GlobalID.from_id(value)


def test_global_id_resolve_type():
    gid = relay.GlobalID(type_name="Fruit", node_id="1")
    type_ = gid.resolve_type(fake_info)
    assert type_ is Fruit


def test_global_id_resolve_node_sync():
    gid = relay.GlobalID(type_name="Fruit", node_id="1")
    fruit = gid.resolve_node_sync(fake_info)
    assert isinstance(fruit, Fruit)
    assert fruit.id == 1
    assert fruit.name == "Banana"


def test_global_id_resolve_node_sync_non_existing():
    gid = relay.GlobalID(type_name="Fruit", node_id="999")
    fruit = gid.resolve_node_sync(fake_info)
    assert_type(fruit, Optional[relay.Node])
    assert fruit is None


def test_global_id_resolve_node_sync_non_existing_but_required():
    gid = relay.GlobalID(type_name="Fruit", node_id="999")
    with pytest.raises(KeyError):
        gid.resolve_node_sync(fake_info, required=True)


def test_global_id_resolve_node_sync_ensure_type():
    gid = relay.GlobalID(type_name="Fruit", node_id="1")
    fruit = gid.resolve_node_sync(fake_info, ensure_type=Fruit)
    assert_type(fruit, Fruit)
    assert isinstance(fruit, Fruit)
    assert fruit.id == 1
    assert fruit.name == "Banana"


def test_global_id_resolve_node_sync_ensure_type_with_union():
    class Foo: ...

    gid = relay.GlobalID(type_name="Fruit", node_id="1")
    fruit = gid.resolve_node_sync(fake_info, ensure_type=Union[Fruit, Foo])
    assert_type(fruit, Union[Fruit, Foo])
    assert isinstance(fruit, Fruit)
    assert fruit.id == 1
    assert fruit.name == "Banana"


def test_global_id_resolve_node_sync_ensure_type_wrong_type():
    class Foo: ...

    gid = relay.GlobalID(type_name="Fruit", node_id="1")
    with pytest.raises(TypeError):
        gid.resolve_node_sync(fake_info, ensure_type=Foo)


async def test_global_id_resolve_node():
    gid = relay.GlobalID(type_name="FruitAsync", node_id="1")
    fruit = await gid.resolve_node(fake_info)
    assert_type(fruit, Optional[relay.Node])
    assert isinstance(fruit, FruitAsync)
    assert fruit.id == 1
    assert fruit.name == "Banana"


async def test_global_id_resolve_node_non_existing():
    gid = relay.GlobalID(type_name="FruitAsync", node_id="999")
    fruit = await gid.resolve_node(fake_info)
    assert_type(fruit, Optional[relay.Node])
    assert fruit is None


async def test_global_id_resolve_node_non_existing_but_required():
    gid = relay.GlobalID(type_name="FruitAsync", node_id="999")
    with pytest.raises(KeyError):
        await gid.resolve_node(fake_info, required=True)


async def test_global_id_resolve_node_ensure_type():
    gid = relay.GlobalID(type_name="FruitAsync", node_id="1")
    fruit = await gid.resolve_node(fake_info, ensure_type=FruitAsync)
    assert_type(fruit, FruitAsync)
    assert isinstance(fruit, FruitAsync)
    assert fruit.id == 1
    assert fruit.name == "Banana"


async def test_global_id_resolve_node_ensure_type_with_union():
    class Foo: ...

    gid = relay.GlobalID(type_name="FruitAsync", node_id="1")
    fruit = await gid.resolve_node(fake_info, ensure_type=Union[FruitAsync, Foo])
    assert_type(fruit, Union[FruitAsync, Foo])
    assert isinstance(fruit, FruitAsync)
    assert fruit.id == 1
    assert fruit.name == "Banana"


async def test_global_id_resolve_node_ensure_type_wrong_type():
    class Foo: ...

    gid = relay.GlobalID(type_name="FruitAsync", node_id="1")
    with pytest.raises(TypeError):
        await gid.resolve_node(fake_info, ensure_type=Foo)


async def test_resolve_async_list_connection():
    @strawberry.type
    class SomeType(relay.Node):
        id: relay.NodeID[int]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[SomeType])
        async def some_type_conn(self) -> AsyncGenerator[SomeType, None]:
            yield SomeType(id=0)
            yield SomeType(id=1)
            yield SomeType(id=2)

    schema = strawberry.Schema(query=Query)
    ret = await schema.execute(
        """\
    query {
      someTypeConn {
        edges {
          node {
            id
          }
        }
      }
    }
    """
    )
    assert ret.errors is None
    assert ret.data == {
        "someTypeConn": {
            "edges": [
                {"node": {"id": to_base64("SomeType", 0)}},
                {"node": {"id": to_base64("SomeType", 1)}},
                {"node": {"id": to_base64("SomeType", 2)}},
            ],
        }
    }


async def test_resolve_async_list_connection_but_sync_after_sliced():
    # We are mimicking an object which is async iterable, but when sliced
    # returns something that is not anymore. This is similar to an already
    # prefetched django QuerySet, which is async iterable by default, but
    # when sliced, since it is already prefetched, will return a list.
    class Slicer:
        def __init__(self, nodes) -> None:
            self.nodes = nodes

        async def __aiter__(self):
            for n in self.nodes:
                yield n

        def __getitem__(self, key):
            return self.nodes[key]

    @strawberry.type
    class SomeType(relay.Node):
        id: relay.NodeID[int]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[SomeType])
        async def some_type_conn(self) -> AsyncIterable[SomeType]:
            return Slicer([SomeType(id=0), SomeType(id=1), SomeType(id=2)])

    schema = strawberry.Schema(query=Query)
    ret = await schema.execute(
        """\
    query {
      someTypeConn {
        edges {
          node {
            id
          }
        }
      }
    }
    """
    )
    assert ret.errors is None
    assert ret.data == {
        "someTypeConn": {
            "edges": [
                {"node": {"id": to_base64("SomeType", 0)}},
                {"node": {"id": to_base64("SomeType", 1)}},
                {"node": {"id": to_base64("SomeType", 2)}},
            ],
        }
    }


def test_overwrite_resolve_id_and_no_node_id():
    @strawberry.type
    class Fruit(relay.Node):
        color: str

        @classmethod
        def resolve_id(cls, root) -> str:
            return "test"  # pragma: no cover

    @strawberry.type
    class Query:
        @strawberry.field
        def fruit(self) -> Fruit:
            return Fruit(color="red")  # pragma: no cover

    strawberry.Schema(query=Query)


def test_list_connection_without_edges_or_page_info(mocker: MagicMock):
    @strawberry.type(name="Connection", description="A connection to a list of items.")
    class DummyListConnectionWithTotalCount(relay.ListConnection[relay.NodeType]):
        @strawberry.field(description="Total quantity of existing nodes.")
        def total_count(self) -> int:
            return -1

    @strawberry.type
    class Query:
        fruits: DummyListConnectionWithTotalCount[Fruit] = relay.connection(
            resolver=fruits_resolver
        )

    mock = mocker.patch("strawberry.relay.types.Edge.resolve_edge")
    schema = strawberry.Schema(query=Query)
    ret = schema.execute_sync(
        """
    query {
      fruits {
        totalCount
      }
    }
    """
    )
    mock.assert_not_called()
    assert ret.errors is None
    assert ret.data == {
        "fruits": {
            "totalCount": -1,
        }
    }


def test_list_connection_with_nested_fragments():
    ret = schema.execute_sync(
        """
    query {
      fruits {
        ...FruitFragment
      }
    }

    fragment FruitFragment on FruitConnection {
        edges {
            node {
                id
            }
        }
    }
    """
    )
    assert ret.errors is None
    assert ret.data == {
        "fruits": {
            "edges": [
                {"node": {"id": "RnJ1aXQ6MQ=="}},
                {"node": {"id": "RnJ1aXQ6Mg=="}},
                {"node": {"id": "RnJ1aXQ6Mw=="}},
                {"node": {"id": "RnJ1aXQ6NA=="}},
                {"node": {"id": "RnJ1aXQ6NQ=="}},
            ]
        }
    }
