import typing

import pytest

import strawberry
from graphql import graphql_sync
from graphql.language import parse
from graphql.subscription import subscribe
from strawberry.permission import BasePermission


def test_raises_graphql_error_when_permission_method_is_missing():
    class IsAuthenticated(BasePermission):
        pass

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self, info) -> str:
            return "patrick"

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = graphql_sync(schema, query)
    assert (
        result.errors[0].message
        == "Permission classes should override has_permission method"
    )


def test_raises_graphql_error_when_permission_is_denied():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, info):
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self, info) -> str:
            return "patrick"

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = graphql_sync(schema, query)
    assert result.errors[0].message == "User is not authenticated"


@pytest.mark.asyncio
async def test_raises_permission_error_for_subscription():
    class IsAdmin(BasePermission):
        message = "You are not authorized"

        def has_permission(self, info):
            return False

    @strawberry.type
    class Query:
        name: str = "Andrew"

    @strawberry.type
    class Subscription:
        @strawberry.subscription(permission_classes=[IsAdmin])
        async def user(self, info) -> typing.AsyncGenerator[str, None]:
            yield "Hello"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { user }"

    result = await subscribe(schema, parse(query))

    assert result.errors[0].message == "You are not authorized"
