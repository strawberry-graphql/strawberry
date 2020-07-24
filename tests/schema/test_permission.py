import typing

import pytest

import strawberry
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

    result = schema.execute_sync(query)
    assert (
        result.errors[0].message
        == "Permission classes should override has_permission method"
    )


def test_raises_graphql_error_when_permission_is_denied():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source, info):
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self, info) -> str:
            return "patrick"

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = schema.execute_sync(query)
    assert result.errors[0].message == "User is not authenticated"


@pytest.mark.asyncio
async def test_raises_permission_error_for_subscription():
    class IsAdmin(BasePermission):
        message = "You are not authorized"

        def has_permission(self, source, info):
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

    result = await schema.subscribe(query)

    assert result.errors[0].message == "You are not authorized"


def test_can_use_source_when_testing_permission():
    class CanSeeEmail(BasePermission):
        message = "Cannot see email for this user"

        def has_permission(self, source, info):
            return source.name.lower() == "patrick"

    @strawberry.type
    class User:
        name: str

        @strawberry.field(permission_classes=[CanSeeEmail])
        def email(self, info) -> str:
            return "patrick.arminio@gmail.com"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, name: str) -> User:
            return User(name=name)

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'

    result = schema.execute_sync(query)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'

    result = schema.execute_sync(query)
    assert result.errors[0].message == "Cannot see email for this user"


def test_can_use_args_when_testing_permission():
    class CanSeeEmail(BasePermission):
        message = "Cannot see email for this user"

        def has_permission(self, source, info, secure):
            return secure

    @strawberry.type
    class User:
        name: str

        @strawberry.field(permission_classes=[CanSeeEmail])
        def email(self, info, secure: bool) -> str:
            return "patrick.arminio@gmail.com"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, name: str) -> User:
            return User(name=name)

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email(secure: true) } }'

    result = schema.execute_sync(query)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "patrick") { email(secure: false) } }'

    result = schema.execute_sync(query)
    assert result.errors[0].message == "Cannot see email for this user"


def test_can_use_on_simple_fields():
    class CanSeeEmail(BasePermission):
        message = "Cannot see email for this user"

        def has_permission(self, source, info):
            return source.name.lower() == "patrick"

    @strawberry.type
    class User:
        name: str
        email: str = strawberry.field(permission_classes=[CanSeeEmail])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'

    result = schema.execute_sync(query)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'

    result = schema.execute_sync(query)
    assert result.errors[0].message == "Cannot see email for this user"
