import sys
from typing import Any, Iterable, List, Optional
from typing_extensions import Self

import pytest

import strawberry
from strawberry.permission import BasePermission
from strawberry.relay import Connection, Node


@strawberry.type
class User(Node):
    id: strawberry.relay.NodeID
    name: str = "John"

    @classmethod
    def resolve_nodes(cls, *, info, node_ids, required):
        return [cls() for _ in node_ids]


@strawberry.type
class UserConnection(Connection[User]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: Iterable[User],
        *,
        info: Any,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
    ) -> Optional[Self]:
        return None


class TestPermission(BasePermission):
    message = "Not allowed"

    def has_permission(self, source, info, **kwargs):
        return False


def test_nullable_connection_with_optional():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(Optional[UserConnection])
        def users(self) -> Optional[List[User]]:
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


pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pipe syntax for union is only available on python 3.10+",
)


def test_nullable_connection_with_pipe():
    @strawberry.type
    class Query:
        @strawberry.relay.connection(UserConnection | None)
        def users(self) -> List[User] | None:
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
            Optional[UserConnection], permission_classes=[TestPermission]
        )
        def users(self) -> Optional[List[User]]:
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
    assert result.errors[0].message == "Not allowed"
