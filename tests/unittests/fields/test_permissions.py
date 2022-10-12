from typing import Any

import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info


def test_permission_classes_basic_fields():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
            return False

    @strawberry.type
    class Query:
        user: str = strawberry.field(permission_classes=[IsAuthenticated])

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "user"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].permission_classes == [IsAuthenticated]


def test_permission_classes():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self) -> str:
            return "patrick"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "user"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].permission_classes == [IsAuthenticated]
