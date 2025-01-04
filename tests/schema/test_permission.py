import re
import textwrap
import typing
from typing import Optional

import pytest

import strawberry
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.exceptions.permission_fail_silently_requires_optional import (
    PermissionFailSilentlyRequiresOptionalError,
)
from strawberry.permission import BasePermission, PermissionExtension
from strawberry.printer import print_schema


def test_raises_graphql_error_when_permission_method_is_missing():
    class IsAuthenticated(BasePermission):
        pass

    error_msg = (
        re.escape("Can't instantiate abstract class IsAuthenticated ") + r"(.*)*"
    )

    with pytest.raises(TypeError, match=error_msg):

        @strawberry.type
        class Query:
            @strawberry.field(permission_classes=[IsAuthenticated])
            def user(self) -> str:  # pragma: no cover
                return "patrick"


def test_raises_graphql_error_when_permission_is_denied():
    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthenticated])
        def user(self) -> str:  # pragma: no cover
            return "patrick"

    schema = strawberry.Schema(query=Query)

    query = "{ user }"

    result = schema.execute_sync(query)
    assert result.errors[0].message == "User is not authenticated"


@pytest.mark.asyncio
async def test_raises_permission_error_for_subscription():
    class IsAdmin(BasePermission):
        message = "You are not authorized"

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> bool:
            return False

    @strawberry.type
    class Query:
        name: str = "Andrew"

    @strawberry.type
    class Subscription:
        @strawberry.subscription(permission_classes=[IsAdmin])
        async def user(self) -> typing.AsyncGenerator[str, None]:  # pragma: no cover
            yield "Hello"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { user }"

    result = await schema.subscribe(query)

    assert result.errors[0].message == "You are not authorized"


@pytest.mark.asyncio
async def test_sync_permissions_work_with_async_resolvers():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["user"] == "Patrick"

    @strawberry.type
    class User:
        name: str
        email: str

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        async def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'
    result = await schema.execute(query, context_value={"user": "Patrick"})
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'
    result = await schema.execute(query, context_value={"user": "Marco"})
    assert result.errors[0].message == "User is not authorized"


def test_can_use_source_when_testing_permission():
    class CanSeeEmail(BasePermission):
        message = "Cannot see email for this user"

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> bool:
            return source.name.lower() == "patrick"

    @strawberry.type
    class User:
        name: str

        @strawberry.field(permission_classes=[CanSeeEmail])
        def email(self) -> str:
            return "patrick.arminio@gmail.com"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, name: str) -> User:
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

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> bool:
            return kwargs.get("secure", False)

    @strawberry.type
    class User:
        name: str

        @strawberry.field(permission_classes=[CanSeeEmail])
        def email(self, secure: bool) -> str:
            return "patrick.arminio@gmail.com"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, name: str) -> User:
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

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> bool:
            return source.name.lower() == "patrick"

    @strawberry.type
    class User:
        name: str
        email: str = strawberry.field(permission_classes=[CanSeeEmail])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'

    result = schema.execute_sync(query)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'

    result = schema.execute_sync(query)
    assert result.errors[0].message == "Cannot see email for this user"


@pytest.mark.asyncio
async def test_dataclass_field_with_async_permission_class():
    class CanSeeEmail(BasePermission):
        message = "Cannot see email for this user"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return source.name.lower() == "patrick"

    @strawberry.type
    class User:
        name: str
        email: str = strawberry.field(permission_classes=[CanSeeEmail])

    @strawberry.type
    class Query:
        @strawberry.field()
        async def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'
    result = await schema.execute(query)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'
    result = await schema.execute(query)
    assert result.errors[0].message == "Cannot see email for this user"


@pytest.mark.asyncio
async def test_async_resolver_with_async_permission_class():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["user"] == "Patrick"

    @strawberry.type
    class User:
        name: str
        email: str

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        async def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'
    result = await schema.execute(query, context_value={"user": "Patrick"})
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'
    result = await schema.execute(query, context_value={"user": "Marco"})
    assert result.errors[0].message == "User is not authorized"


@pytest.mark.asyncio
async def test_sync_resolver_with_async_permission_class():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["user"] == "Patrick"

    @strawberry.type
    class User:
        name: str
        email: str

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)

    query = '{ user(name: "patrick") { email } }'
    result = await schema.execute(query, context_value={"user": "Patrick"})
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"

    query = '{ user(name: "marco") { email } }'
    result = await schema.execute(query, context_value={"user": "Marco"})
    assert result.errors[0].message == "User is not authorized"


@pytest.mark.asyncio
async def test_mixed_sync_and_async_permission_classes():
    class IsAuthorizedAsync(BasePermission):
        message = "User is not authorized (async)"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context.get("passAsync", False)

    class IsAuthorizedSync(BasePermission):
        message = "User is not authorized (sync)"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context.get("passSync", False)

    @strawberry.type
    class User:
        name: str
        email: str

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorizedAsync, IsAuthorizedSync])
        def user(self, name: str) -> User:
            return User(name=name, email="patrick.arminio@gmail.com")

    schema = strawberry.Schema(query=Query)
    query = '{ user(name: "patrick") { email } }'

    context = {"passAsync": False, "passSync": False}
    result = await schema.execute(query, context_value=context)
    assert result.errors[0].message == "User is not authorized (async)"

    context = {"passAsync": True, "passSync": False}
    result = await schema.execute(query, context_value=context)
    assert result.errors[0].message == "User is not authorized (sync)"

    context = {"passAsync": False, "passSync": True}
    result = await schema.execute(query, context_value=context)
    assert result.errors[0].message == "User is not authorized (async)"

    context = {"passAsync": True, "passSync": True}
    result = await schema.execute(query, context_value=context)
    assert result.data["user"]["email"] == "patrick.arminio@gmail.com"


def test_permissions_with_custom_extensions():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"
        error_extensions = {"code": "UNAUTHORIZED"}

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)
    query = "{ name }"

    result = schema.execute_sync(query)
    assert result.errors[0].message == "User is not authorized"
    assert result.errors[0].extensions
    assert result.errors[0].extensions["code"] == "UNAUTHORIZED"


def test_permissions_with_custom_extensions_on_custom_error():
    class CustomError(StrawberryGraphQLError):
        def __init__(self, message: str):
            super().__init__(message, extensions={"general_info": "CUSTOM_ERROR"})

    class IsAuthorized(BasePermission):
        message = "User is not authorized"
        error_class = CustomError
        error_extensions = {"code": "UNAUTHORIZED"}

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)
    query = "{ name }"

    result = schema.execute_sync(query)

    assert result.errors[0].message == "User is not authorized"
    assert result.errors[0].extensions
    assert result.errors[0].extensions["code"] == "UNAUTHORIZED"
    assert result.errors[0].extensions["general_info"] == "CUSTOM_ERROR"


def test_silent_permissions_optional():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
        )
        def name(self) -> Optional[str]:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)
    query = "{ name }"
    result = schema.execute_sync(query)

    assert result.data["name"] is None
    assert result.errors is None


def test_silent_permissions_optional_list():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
        )
        def names(self) -> Optional[list[str]]:  # pragma: no cover
            return ["ABC"]

    schema = strawberry.Schema(query=Query)
    query = "{ names }"
    result = schema.execute_sync(query)

    assert result.data["names"] == []
    assert result.errors is None


def test_silent_permissions_list():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
        )
        def names(self) -> list[str]:  # pragma: no cover
            return ["ABC"]

    schema = strawberry.Schema(query=Query)
    query = "{ names }"
    result = schema.execute_sync(query)

    assert result.data["names"] == []
    assert result.errors is None


@pytest.mark.raises_strawberry_exception(
    PermissionFailSilentlyRequiresOptionalError,
    match="Cannot use fail_silently=True with a non-optional or non-list field",
)
def test_silent_permissions_incompatible_types():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(
            self, source, info, **kwargs: typing.Any
        ) -> bool:  # pragma: no cover
            return False

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
        )
        def name(self) -> User:  # pragma: no cover
            return User(name="ABC")

    strawberry.Schema(query=Query)


def test_permission_directives_added():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(
            self, source, info, **kwargs: typing.Any
        ) -> bool:  # pragma: no cover
            return False

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAuthorized()])])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAuthorized on FIELD_DEFINITION

    type Query {
      name: String! @isAuthorized
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_permission_directives_not_added_on_field():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(
            self, source, info, **kwargs: typing.Any
        ) -> bool:  # pragma: no cover
            return False

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    expected_output = """
    type Query {
      name: String!
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_basic_permission_access_inputs():
    class IsAuthorized(BasePermission):
        message = "User is not authorized"

        def has_permission(
            self, source, info, **kwargs: typing.Any
        ) -> bool:  # pragma: no cover
            return kwargs["a_key"] == "secret"

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[IsAuthorized])
        def name(self, a_key: str) -> str:  # pragma: no cover
            return "Erik"

    schema = strawberry.Schema(query=Query)

    query = '{ name(aKey: "example") }'
    result = schema.execute_sync(query)

    assert result.errors[0].message == "User is not authorized"

    query = '{ name(aKey: "secret") }'

    result = schema.execute_sync(query)

    assert result.data["name"] == "Erik"
