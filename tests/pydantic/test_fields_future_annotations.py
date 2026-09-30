from __future__ import annotations

from typing import Annotated, Any

import pydantic

import strawberry
from strawberry.types.base import get_object_definition

# Types are defined at module level: with postponed annotations, Strawberry
# resolves the resolvers' string annotations from the module namespace.


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: Annotated[
        str,
        strawberry.field(
            name="fullName",
            description="The full name",
            deprecation_reason="Use displayName",
        ),
    ]
    email: Annotated[str, strawberry.field(permission_classes=[IsAdmin])]
    password: strawberry.Private[str]


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Ada", email="ada@example.com", password="secret")


schema = strawberry.Schema(query=Query)


def test_private_fields_are_excluded():
    assert "password" not in str(schema)

    result = schema.execute_sync("{ user { password } }")

    assert result.errors
    assert result.errors[0].message == "Cannot query field 'password' on type 'User'."


def test_annotated_permissions_are_enforced():
    result = schema.execute_sync("{ user { fullName email } }")

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_annotated_field_options_are_used():
    name_field = next(
        field
        for field in get_object_definition(User, strict=True).fields
        if field.python_name == "name"
    )

    assert name_field.graphql_name == "fullName"
    assert name_field.description == "The full name"
    assert name_field.deprecation_reason == "Use displayName"
