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


@pytest.mark.parametrize(
    ("field_max_results", "schema_max_results"),
    [(5, 100), (None, 5)],
)
def test_max_results_with_before(
    field_max_results: int | None,
    schema_max_results: int,
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
            return [User(id=str(i)) for i in range(20)]

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(relay_max_results=schema_max_results),
    )
    query = """
      query ($before: String) {
        users(before: $before) {
          edges {
            node {
              id
            }
          }
          pageInfo {
            hasNextPage
            hasPreviousPage
          }
        }
      }
    """

    result = schema.execute_sync(
        query, variable_values={"before": to_base64("arrayconnection", 15)}
    )
    assert result.errors is None
    assert result.data == {
        "users": {
            "edges": [{"node": {"id": to_base64("User", i)}} for i in range(5)],
            "pageInfo": {"hasNextPage": True, "hasPreviousPage": False},
        }
    }


@pytest.mark.parametrize("argument", ["before", "after"])
@pytest.mark.parametrize("offset", ["-5", "abc", " 1", "+1", ""])
@pytest.mark.parametrize("as_iterator", [False, True])
def test_invalid_cursor_offsets_are_rejected(
    argument: str, offset: str, as_iterator: bool
):
    @strawberry.type
    class User(Node):
        id: strawberry.relay.NodeID[str]

    @strawberry.type
    class Query:
        @strawberry.relay.connection(ListConnection[User], max_results=5)
        def users(self) -> Iterable[User]:
            users = [User(id=str(i)) for i in range(20)]
            return iter(users) if as_iterator else users

    schema = strawberry.Schema(query=Query)
    query = f"""
      query ($cursor: String) {{
        users({argument}: $cursor) {{
          edges {{
            node {{
              id
            }}
          }}
        }}
      }}
    """

    result = schema.execute_sync(
        query, variable_values={"cursor": to_base64("arrayconnection", offset)}
    )
    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == (
        f"Argument '{argument}' contains a non-existing value."
    )
