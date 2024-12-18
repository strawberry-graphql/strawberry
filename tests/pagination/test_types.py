from typing import AsyncGenerator, AsyncIterable, List

from pytest_mock import MockerFixture

import strawberry
from strawberry.pagination.fields import connection
from strawberry.pagination.types import ListConnection, NodeType


async def test_resolve_async_list_connection():
    @strawberry.type
    class SomeType:
        id: int

    @strawberry.type
    class Query:
        @connection(ListConnection[SomeType])
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
                {"node": {"id": 0}},
                {"node": {"id": 1}},
                {"node": {"id": 2}},
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
    class SomeType:
        id: int

    @strawberry.type
    class Query:
        @connection(ListConnection[SomeType])
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
                {"node": {"id": 0}},
                {"node": {"id": 1}},
                {"node": {"id": 2}},
            ],
        }
    }


def test_list_connection_without_edges_or_page_info_should_not_call_resolver(
    mocker: MockerFixture,
):
    resolve_edge_mock = mocker.patch("strawberry.pagination.types.Edge.resolve_edge")

    @strawberry.type(name="Connection", description="A connection to a list of items.")
    class DummyListConnectionWithTotalCount(ListConnection[NodeType]):
        @strawberry.field(description="Total quantity of existing nodes.")
        def total_count(self) -> int:
            return -1

    @strawberry.type
    class Fruit:
        id: int

    def fruits_resolver() -> List[Fruit]:
        return [Fruit(id=1), Fruit(id=2), Fruit(id=3), Fruit(id=4), Fruit(id=5)]

    fruits_resolver_spy = mocker.spy(fruits_resolver, "__call__")

    @strawberry.type
    class Query:
        fruits: DummyListConnectionWithTotalCount[Fruit] = connection(
            resolver=fruits_resolver
        )

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
    assert ret.errors is None
    assert ret.data == {
        "fruits": {
            "totalCount": -1,
        }
    }

    resolve_edge_mock.assert_not_called()
    fruits_resolver_spy.assert_not_called()
