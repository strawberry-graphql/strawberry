from typing import Any

import pytest
from asgiref.sync import sync_to_async

import strawberry
from strawberry.permission import BasePermission


def test_permission_classes_basic_fields():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(
            self, source: Any, info: strawberry.Info, **kwargs: Any
        ) -> bool:
            return False

    @strawberry.type
    class Query:
        user: str = strawberry.field(permission_classes=[IsAuthenticated])

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "user"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].permission_classes == [IsAuthenticated]


def test_permission_classes():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(
            self, source: Any, info: strawberry.Info, **kwargs: Any
        ) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self) -> str:
            return "patrick"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "user"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].permission_classes == [IsAuthenticated]


@pytest.mark.asyncio
async def test_permission_classes_async():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        @sync_to_async
        def has_permission(
            self, source: Any, info: strawberry.Info, **kwargs: Any
        ) -> bool:
            return True

    @sync_to_async
    def resolver() -> str:
        return "patrick"

    @strawberry.type
    class Query:
        user: str = strawberry.field(
            resolver=resolver, permission_classes=[IsAuthenticated]
        )

    schema = strawberry.Schema(Query)

    result = await schema.execute("query { user }")

    assert not result.errors
