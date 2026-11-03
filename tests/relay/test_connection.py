from collections.abc import Iterable
from typing import Annotated, Any, Optional, Self

import pytest

import strawberry
from strawberry.permission import BasePermission
from strawberry.relay import Connection, Node, PageInfo, to_base64
from strawberry.relay.types import Edge, ListConnection
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class User(Node):
    id: strawberry.relay.NodeID
    name: str = "John"

    @classmethod
    def resolve_nodes(
        cls, *, info: strawberry.Info, node_ids: list[Any], required: bool
    ) -> list[Self]:
        return [cls() for _ in node_ids]


@strawberry.type
class EmptyUserConnection(Connection[User]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: Iterable[User],
        *,
        info: Any,
        after: str | None = None,
        before: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> Self | None:
        return None


@strawberry.type
class UserConnection(Connection[User]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: Iterable[User],
        *,
        info: Any,
        after: str | None = None,
        before: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> Self | None:
        user_node_id = to_base64(User, "1")
        return cls(
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            edges=[Edge(cursor=user_node_id, node=User(id=user_node_id))],
        )


class TestPermission(BasePermission):
    message = "Not allowed"

    def has_permission(self, source, info, **kwargs: Any):
        return False


def test_nullable_connection_with_optional():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(Optional[EmptyUserConnection])
        def users(self) -> list[User] | None:
            return None

    schema = strawberry.Schema(query=Query)
    query = """
        query {
            users {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    """

    result = schema.execute_sync(query)
    assert result.data == {"users": None}
    assert not result.errors


def test_lazy_connection():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(
            Optional[
                Annotated[
                    "UserConnection", strawberry.lazy("tests.relay.test_connection")
                ]
            ]
        )
        def users(self) -> list[User] | None:
            return None

    schema = strawberry.Schema(query=Query)
    query = """
            query {
                users {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        """

    result = schema.execute_sync(query)
    assert result.data == {"users": {"edges": [{"node": {"name": "John"}}]}}
    assert not result.errors


def test_lazy_optional_connection():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(
            Optional[
                Annotated[
                    "EmptyUserConnection",
                    strawberry.lazy("tests.relay.test_connection"),
                ]
            ]
        )
        def users(self) -> list[User] | None:
            return None

    schema = strawberry.Schema(query=Query)
    query = """
            query {
                users {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        """

    result = schema.execute_sync(query)
    assert result.data == {"users": None}
    assert not result.errors


def test_nullable_connection_with_pipe():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(EmptyUserConnection | None)
        def users(self) -> list[User] | None:
            return None

    schema = strawberry.Schema(query=Query)
    query = """
        query {
            users {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    """

    result = schema.execute_sync(query)
    assert result.data == {"users": None}
    assert not result.errors


def test_nullable_connection_with_permission():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(
            Optional[EmptyUserConnection], permission_classes=[TestPermission]
        )
        def users(self) -> list[User] | None:  # pragma: no cover
            pytest.fail("Should not have been called...")

    schema = strawberry.Schema(query=Query)
    query = """
        query {
            users {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    """

    result = schema.execute_sync(query)
    assert result.data == {"users": None}
    assert result.errors[0].message == "Not allowed"


@pytest.mark.parametrize(
    ("field_max_results", "schema_max_results", "results", "expected"),
    [
        (5, 100, 5, 5),
        (5, 2, 5, 5),
        (5, 100, 10, 5),
        (5, 2, 10, 5),
        (5, 100, 0, 0),
        (5, 2, 0, 0),
        (None, 100, 5, 5),
        (None, 2, 5, 2),
    ],
)
def test_max_results(
    field_max_results: int | None,
    schema_max_results: int,
    results: int,
    expected: int,
):
    @strawberry.type
    class User(Node):
        id: strawberry.relay.NodeID[str]

    @strawberry.type
    class Query:
        @strawberry.relay.connection(
            ListConnection[User],
            max_results=field_max_results,
        )
        def users(self) -> list[User]:
            return [User(id=str(i)) for i in range(results)]

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(relay_max_results=schema_max_results),
    )
    query = """
      query {
        users {
          edges {
            node {
              id
            }
          }
        }
      }
    """

    result = schema.execute_sync(query)
    assert result.data is not None
    assert isinstance(result.data["users"]["edges"], list)
    assert len(result.data["users"]["edges"]) == expected


def test_connection_with_offset():
    @strawberry.type
    class Item(Node):
        id: strawberry.relay.NodeID[str]

    @strawberry.type
    class Query:
        @strawberry.relay.connection(ListConnection[Item])
        def items(self) -> list[Item]:
            return [Item(id=str(i)) for i in range(10)]

    schema = strawberry.Schema(query=Query)
    query = """
      query ($offset: Int, $first: Int, $last: Int) {
        items(offset: $offset, first: $first, last: $last) {
          pageInfo {
            hasPreviousPage
            hasNextPage
            startCursor
            endCursor
          }
          edges {
            node {
              id
            }
          }
        }
      }
    """

    res = schema.execute_sync(query, variable_values={"offset": 3, "first": 2})
    assert not res.errors
    assert res.data == {
        "items": {
            "pageInfo": {
                "hasPreviousPage": True,
                "hasNextPage": True,
                "startCursor": to_base64("arrayconnection", "3"),
                "endCursor": to_base64("arrayconnection", "4"),
            },
            "edges": [
                {"node": {"id": to_base64("Item", "3")}},
                {"node": {"id": to_base64("Item", "4")}},
            ],
        }
    }

    res_last = schema.execute_sync(query, variable_values={"offset": 8, "last": 2})
    assert not res_last.errors
    assert res_last.data == {
        "items": {
            "pageInfo": {
                "hasPreviousPage": True,
                "hasNextPage": False,
                "startCursor": to_base64("arrayconnection", "8"),
                "endCursor": to_base64("arrayconnection", "9"),
            },
            "edges": [
                {"node": {"id": to_base64("Item", "8")}},
                {"node": {"id": to_base64("Item", "9")}},
            ],
        }
    }


async def test_async_connection_with_offset():
    @strawberry.type
    class Item(Node):
        id: strawberry.relay.NodeID[str]

    @strawberry.type
    class Query:
        @strawberry.relay.connection(ListConnection[Item])
        async def items(self) -> list[Item]:
            return [Item(id=str(i)) for i in range(10)]

    schema = strawberry.Schema(query=Query)
    query = """
      query ($offset: Int, $first: Int) {
        items(offset: $offset, first: $first) {
          edges {
            node {
              id
            }
          }
        }
      }
    """

    res = await schema.execute(query, variable_values={"offset": 3, "first": 2})
    assert not res.errors
    assert res.data == {
        "items": {
            "edges": [
                {"node": {"id": to_base64("Item", "3")}},
                {"node": {"id": to_base64("Item", "4")}},
            ]
        }
    }


async def test_custom_connection_legacy_signature_without_offset():
    @strawberry.type
    class Item(Node):
        id: strawberry.relay.NodeID[str]

    @strawberry.type
    class CustomLegacyConnection(strawberry.relay.Connection[Item]):
        @classmethod
        def resolve_connection(
            cls,
            nodes: Iterable[Item],
            *,
            info: strawberry.Info,
            before: str | None = None,
            after: str | None = None,
            first: int | None = None,
            last: int | None = None,
            max_results: int | None = None,
        ) -> Self:
            edges = [
                strawberry.relay.Edge(
                    cursor=to_base64("Item", node.id),
                    node=node,
                )
                for node in nodes
            ]
            return cls(
                page_info=strawberry.relay.PageInfo(
                    has_next_page=False,
                    has_previous_page=False,
                    start_cursor=edges[0].cursor if edges else None,
                    end_cursor=edges[-1].cursor if edges else None,
                ),
                edges=edges,
            )

    @strawberry.type
    class Query:
        @strawberry.relay.connection(CustomLegacyConnection)
        def sync_items(self) -> list[Item]:
            return [Item(id="1"), Item(id="2")]

        @strawberry.relay.connection(CustomLegacyConnection)
        async def async_items(self) -> list[Item]:
            return [Item(id="3"), Item(id="4")]

    schema = strawberry.Schema(query=Query)
    query = """
      query {
        syncItems {
          edges {
            node {
              id
            }
          }
        }
        asyncItems {
          edges {
            node {
              id
            }
          }
        }
      }
    """

    res = await schema.execute(query)
    assert not res.errors
    assert res.data == {
        "syncItems": {
            "edges": [
                {"node": {"id": to_base64("Item", "1")}},
                {"node": {"id": to_base64("Item", "2")}},
            ]
        },
        "asyncItems": {
            "edges": [
                {"node": {"id": to_base64("Item", "3")}},
                {"node": {"id": to_base64("Item", "4")}},
            ]
        },
    }
