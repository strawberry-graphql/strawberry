from typing import Optional, Union

import strawberry
from strawberry.permission import BasePermission
from strawberry.relay import Connection, Node, connection


@strawberry.type
class User(Node):
    name: str = "John"

    @classmethod
    def resolve_nodes(cls, *, info, node_ids, required):
        return [cls() for _ in node_ids]


class TestPermission(BasePermission):
    message = "Not allowed"

    def has_permission(self, source, info, **kwargs):
        return False


def test_nullable_connection_with_optional():
    @strawberry.type
    class Query:
        @connection
        def users(self) -> Optional[Connection[User]]:
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


def test_nullable_connection_with_union():
    @strawberry.type
    class Query:
        @connection
        def users(self) -> Union[Connection[User], None]:
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
        @strawberry.permission_classes([TestPermission])
        @connection
        def users(self) -> Optional[Connection[User]]:
            return Connection[User](edges=[], page_info=None)

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


def test_non_nullable_connection():
    @strawberry.type
    class Query:
        @connection
        def users(self) -> Connection[User]:
            return Connection[User](edges=[], page_info=None)

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
    assert result.data == {"users": {"edges": []}}
    assert not result.errors
