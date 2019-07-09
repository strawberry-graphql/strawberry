import pytest

from graphql import graphql, graphql_sync

import strawberry
from strawberry.permission import BasePermission


def test_raises_graphql_error_when_has_permission_is_not_defined():

    class IsAuthenticated(BasePermission):
        pass

    @strawberry.type
    class Query:

        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self, info) -> str:
            return 'patrick'

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = graphql_sync(schema, query)
    assert result.errors[0].message == "Permission classes should override has_permission method"


def test_raises_graphql_error_when_permission_is_denied():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, info):
            return False

    @strawberry.type
    class Query:

        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self, info) -> str:
            return 'patrick'

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = graphql_sync(schema, query)
    assert result.errors[0].message == "User is not authenticated"
