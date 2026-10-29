import re
import textwrap
import typing

import pytest

import strawberry
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.exceptions.permission_fail_silently_requires_optional import (
    PermissionFailSilentlyRequiresOptionalError,
)
from strawberry.permission import BasePermission, OrPermission, PermissionExtension
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location
from strawberry.types import ExecutionResult
from strawberry.utils.aio import aclosing


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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

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
        def name(self) -> str | None:  # pragma: no cover
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
        def names(self) -> list[str] | None:  # pragma: no cover
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


def test_permission_directives_reused_across_fields():
    class IsAuthorized(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        first: str = strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()])]
        )
        second: str = strawberry.field(
            extensions=[PermissionExtension([IsAuthorized()])]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAuthorized on FIELD_DEFINITION

    type Query {
      first: String! @isAuthorized
      second: String! @isAuthorized
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_permission_directive_can_be_overridden_on_an_instance():
    @strawberry.schema_directive(
        name="requiresRole", locations=[Location.FIELD_DEFINITION]
    )
    class RequiresRole:
        role: str

    class IsAuthorized(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    permission = IsAuthorized()
    permission._schema_directive = RequiresRole(role="member")

    @strawberry.type
    class Query:
        name: str = strawberry.field(extensions=[PermissionExtension([permission])])

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @requiresRole(role: String!) on FIELD_DEFINITION

    type Query {
      name: String! @requiresRole(role: "member")
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_permission_directive_can_be_inherited():
    @strawberry.schema_directive(
        name="requiresRole", locations=[Location.FIELD_DEFINITION]
    )
    class RequiresRole:
        role: str

    class IsAuthorized(BasePermission):
        _schema_directive = RequiresRole(role="member")

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsMember(IsAuthorized): ...

    @strawberry.type
    class Query:
        name: str = strawberry.field(extensions=[PermissionExtension([IsMember()])])

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @requiresRole(role: String!) on FIELD_DEFINITION

    type Query {
      name: String! @requiresRole(role: "member")
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_permission_directive_collision_names_permission_classes():
    def has_permission(
        self: BasePermission, source, info, **kwargs: typing.Any
    ) -> bool:
        return True

    First = type(
        "CanAccess",
        (BasePermission,),
        {"__module__": "permissions.first", "has_permission": has_permission},
    )
    Second = type(
        "CanAccess",
        (BasePermission,),
        {"__module__": "permissions.second", "has_permission": has_permission},
    )

    @strawberry.type
    class Query:
        first: str = strawberry.field(extensions=[PermissionExtension([First()])])
        second: str = strawberry.field(extensions=[PermissionExtension([Second()])])

    with pytest.raises(
        ValueError,
        match=(
            r"Schema directive '@canAccess' is defined by both schema directive "
            r"'permissions\.first\.CanAccess' and schema directive "
            r"'permissions\.second\.CanAccess'"
        ),
    ):
        strawberry.Schema(query=Query)


def test_or_permission_directive_shared_across_fields():
    class IsA(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsB(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        first: str = strawberry.field(extensions=[PermissionExtension([IsA() | IsB()])])
        second: str = strawberry.field(
            extensions=[PermissionExtension([IsA() | IsB()])]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAOrIsB on FIELD_DEFINITION

    type Query {
      first: String! @isAOrIsB
      second: String! @isAOrIsB
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_does_not_depend_on_operand_order():
    class IsA(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsB(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        first: str = strawberry.field(extensions=[PermissionExtension([IsA() | IsB()])])
        second: str = strawberry.field(
            extensions=[PermissionExtension([IsB() | IsA()])]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAOrIsB on FIELD_DEFINITION

    type Query {
      first: String! @isAOrIsB
      second: String! @isAOrIsB
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_is_flat_for_chained_and_nested_operands():
    class IsA(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsB(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsC(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        chained: str = strawberry.field(
            extensions=[PermissionExtension([IsA() | IsB() | IsC()])]
        )
        nested: str = strawberry.field(
            extensions=[PermissionExtension([IsC() | (IsB() | IsA())])]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAOrIsBOrIsC on FIELD_DEFINITION

    type Query {
      chained: String! @isAOrIsBOrIsC
      nested: String! @isAOrIsBOrIsC
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_next_to_other_permission_directives():
    class IsAuthenticated(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsOwner(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsStaff(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            extensions=[PermissionExtension([IsAuthenticated(), IsOwner() | IsStaff()])]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @isAuthenticated on FIELD_DEFINITION

    directive @isOwnerOrIsStaff on FIELD_DEFINITION

    type Query {
      name: String! @isAuthenticated @isOwnerOrIsStaff
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_with_auto_camel_case_disabled():
    class IsA(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsB(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        name: str = strawberry.field(extensions=[PermissionExtension([IsA() | IsB()])])

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )

    expected_output = """
    directive @IsAOrIsB on FIELD_DEFINITION

    type Query {
      name: String! @IsAOrIsB
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_not_added_when_directives_are_disabled():
    class IsA(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class IsB(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    @strawberry.type
    class Query:
        name: str = strawberry.field(
            extensions=[PermissionExtension([IsA() | IsB()], use_directives=False)]
        )

    schema = strawberry.Schema(query=Query)

    expected_output = """
    type Query {
      name: String!
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()


def test_or_permission_directive_collision_names_permission_classes():
    def has_permission(
        self: BasePermission, source, info, **kwargs: typing.Any
    ) -> bool:
        return True

    FirstCanAccess = type(
        "CanAccess",
        (BasePermission,),
        {"__module__": "permissions.first", "has_permission": has_permission},
    )
    SecondCanAccess = type(
        "CanAccess",
        (BasePermission,),
        {"__module__": "permissions.second", "has_permission": has_permission},
    )
    IsOwner = type(
        "IsOwner",
        (BasePermission,),
        {"__module__": "permissions.owner", "has_permission": has_permission},
    )

    @strawberry.type
    class Query:
        first: str = strawberry.field(
            extensions=[PermissionExtension([FirstCanAccess() | IsOwner()])]
        )
        second: str = strawberry.field(
            extensions=[PermissionExtension([SecondCanAccess() | IsOwner()])]
        )

    with pytest.raises(
        ValueError,
        match=(
            r"Schema directive '@canAccessOrIsOwner' is defined by both schema "
            r"directive 'strawberry\.permission\.CanAccessOrIsOwner"
            r"\(permissions\.first\.CanAccess \| permissions\.owner\.IsOwner\)' "
            r"and schema directive 'strawberry\.permission\.CanAccessOrIsOwner"
            r"\(permissions\.second\.CanAccess \| permissions\.owner\.IsOwner\)'"
        ),
    ):
        strawberry.Schema(query=Query)


def test_or_permission_subclass_name_collides_with_derived_directive_name():
    class Admin(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class Owner(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class AdminOrOwner(OrPermission):
        pass

    @strawberry.type
    class Query:
        named: str = strawberry.field(
            extensions=[PermissionExtension([AdminOrOwner(Admin(), Owner())])]
        )
        derived: str = strawberry.field(
            extensions=[PermissionExtension([Admin() | Owner()])]
        )

    with pytest.raises(
        ValueError, match=r"Schema directive '@adminOrOwner' is defined by both"
    ):
        strawberry.Schema(query=Query)


def test_or_permission_of_the_same_class_with_different_arguments():
    class HasRole(BasePermission):
        def __init__(self, role: str) -> None:
            self.role = role

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == self.role

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([HasRole("admin") | HasRole("editor")])]
        )
        def name(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @hasRoleOrHasRole on FIELD_DEFINITION

    type Query {
      name: String! @hasRoleOrHasRole
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()

    result = schema.execute_sync("{ name }", context_value={"role": "editor"})
    assert result.errors is None
    assert result.data == {"name": "ABC"}

    result = schema.execute_sync("{ name }", context_value={"role": "guest"})
    assert result.data is None
    assert result.errors is not None


@pytest.mark.parametrize(
    ("first_allows", "second_allows", "granted"),
    [
        (True, True, True),
        (True, False, True),
        (False, True, True),
        (False, False, False),
    ],
)
def test_or_permission_grants_access_when_any_permission_passes(
    first_allows: bool, second_allows: bool, granted: bool
):
    class Flag(BasePermission):
        def __init__(self, allowed: bool, message: str) -> None:
            self.allowed = allowed
            self.message = message

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return self.allowed

    calls = 0

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[
                PermissionExtension(
                    [
                        Flag(first_allows, "first denied")
                        | Flag(second_allows, "second denied")
                    ]
                )
            ]
        )
        def name(self) -> str:
            nonlocal calls
            calls += 1
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name }")

    if granted:
        assert result.errors is None
        assert result.data == {"name": "ABC"}
        assert calls == 1
    else:
        assert result.data is None
        assert result.errors is not None
        assert [error.message for error in result.errors] == ["first denied"]
        assert calls == 0


def test_or_permission_stops_at_the_first_permission_that_passes():
    checked: list[str] = []

    class Recorder(BasePermission):
        def __init__(self, name: str, allowed: bool) -> None:
            self.name = name
            self.allowed = allowed

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            checked.append(self.name)
            return self.allowed

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[
                PermissionExtension(
                    [Recorder("a", False) | Recorder("b", True) | Recorder("c", True)]
                )
            ]
        )
        def name(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name }")

    assert result.errors is None
    assert checked == ["a", "b"]


def test_or_permission_forwards_arguments_to_every_permission():
    seen: list[typing.Any] = []

    class CheckKey(BasePermission):
        def __init__(self, expected: str) -> None:
            self.expected = expected

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            seen.append(kwargs["a_key"])
            return kwargs["a_key"] == self.expected

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([CheckKey("one") | CheckKey("two")])]
        )
        def name(self, a_key: str) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ name(aKey: "two") }')

    assert result.errors is None
    assert seen == ["two", "two"]


def test_or_permission_fail_silently_returns_none():
    class IsA(BasePermission):
        message = "A denied"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    class IsB(BasePermission):
        message = "B denied"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsA() | IsB()], fail_silently=True)]
        )
        def name(self) -> str | None:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name }")

    assert result.errors is None
    assert result.data == {"name": None}


@pytest.mark.asyncio
async def test_or_permission_subclass_overriding_has_permission_is_honored():
    calls = 0

    class Allowed(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class AsyncAllowed(BasePermission):
        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return True

    class StrictDeny(OrPermission):
        message = "strictly denied"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([StrictDeny(Allowed(), AsyncAllowed())])]
        )
        def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "strictly denied"
    assert calls == 0


@pytest.mark.asyncio
async def test_or_permission_with_async_permission_and_sync_resolver():
    class IsAdmin(BasePermission):
        message = "Not an admin"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "admin"

    class IsOwner(BasePermission):
        message = "Not the owner"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "owner"

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsOwner() | IsAdmin()])])
        def name(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    for role in ("owner", "admin"):
        result = await schema.execute("{ name }", context_value={"role": role})
        assert result.errors is None
        assert result.data == {"name": "ABC"}

    result = await schema.execute("{ name }", context_value={"role": "guest"})
    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "Not the owner"


@pytest.mark.asyncio
async def test_or_permission_with_async_permission_and_async_resolver():
    class IsAdmin(BasePermission):
        message = "Not an admin"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "admin"

    class IsOwner(BasePermission):
        message = "Not the owner"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "owner"

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAdmin() | IsOwner()])])
        async def name(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    for role in ("owner", "admin"):
        result = await schema.execute("{ name }", context_value={"role": role})
        assert result.errors is None
        assert result.data == {"name": "ABC"}

    result = await schema.execute("{ name }", context_value={"role": "guest"})
    assert result.data is None
    assert result.errors is not None
    assert result.errors[0].message == "Not an admin"


@pytest.mark.asyncio
async def test_or_permission_of_sync_permissions_runs_on_both_execution_paths():
    class IsAdmin(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "admin"

    class IsOwner(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "owner"

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAdmin() | IsOwner()])])
        def name(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    sync_result = schema.execute_sync("{ name }", context_value={"role": "owner"})
    async_result = await schema.execute("{ name }", context_value={"role": "owner"})

    assert sync_result.data == {"name": "ABC"}
    assert async_result.data == {"name": "ABC"}


def test_or_permission_with_sync_permission_returning_awaitable_denies_access():
    calls = 0

    class DenyViaAwaitable(BasePermission):
        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> typing.Any:
            async def result() -> bool:
                return True

            return result()

    class IsAdmin(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAdmin() | DenyViaAwaitable()])]
        )
        def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert "returned an awaitable" in result.errors[0].message
    assert "DenyViaAwaitable" in result.errors[0].message
    assert calls == 0


@pytest.mark.asyncio
async def test_or_permission_with_sync_permission_returning_awaitable_denies_access_on_async_execution():
    calls = 0

    class DenyViaAwaitable(BasePermission):
        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> typing.Any:
            async def result() -> bool:
                return True

            return result()

    class IsAdmin(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAdmin() | DenyViaAwaitable()])]
        )
        def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert "returned an awaitable" in result.errors[0].message
    assert "DenyViaAwaitable" in result.errors[0].message
    assert calls == 0


@pytest.mark.asyncio
async def test_or_permission_with_sync_permission_returning_awaitable_denies_access_with_async_resolver():
    calls = 0

    class DenyViaAwaitable(BasePermission):
        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> typing.Any:
            async def result() -> bool:
                return True

            return result()

    class IsAdmin(BasePermission):
        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([IsAdmin() | DenyViaAwaitable()])]
        )
        async def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert "returned an awaitable" in result.errors[0].message
    assert "DenyViaAwaitable" in result.errors[0].message
    assert calls == 0


def test_or_permission_uses_custom_error_of_the_first_permission():
    class CustomError(StrawberryGraphQLError):
        def __init__(self, message: str):
            super().__init__(message, extensions={"general_info": "CUSTOM_ERROR"})

    class IsAdmin(BasePermission):
        message = "Not an admin"
        error_class = CustomError
        error_extensions = {"code": "NOT_ADMIN"}

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    class IsOwner(BasePermission):
        message = "Not the owner"
        error_extensions = {"code": "NOT_OWNER"}

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAdmin() | IsOwner()])])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name }")

    assert result.errors is not None
    assert result.errors[0].message == "Not an admin"
    assert result.errors[0].extensions == {
        "general_info": "CUSTOM_ERROR",
        "code": "NOT_ADMIN",
    }


def test_or_permission_uses_custom_on_unauthorized_of_the_first_permission():
    class CustomPermissionError(PermissionError):
        pass

    class IsAdmin(BasePermission):
        message = "Not an admin"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

        def on_unauthorized(self) -> None:
            raise CustomPermissionError(self.message)

    class IsOwner(BasePermission):
        message = "Not the owner"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAdmin() | IsOwner()])])
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name }")

    assert result.errors is not None
    assert result.errors[0].message == "Not an admin"
    assert isinstance(result.errors[0].original_error, CustomPermissionError)


def test_or_permission_subclass_uses_its_own_error_and_directive_name():
    class IsAdmin(BasePermission):
        message = "Not an admin"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    class IsOwner(BasePermission):
        message = "Not the owner"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return False

    class AdminOrOwner(OrPermission):
        message = "You need to be an admin or the owner"

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension([AdminOrOwner(IsAdmin(), IsOwner())])]
        )
        def name(self) -> str:  # pragma: no cover
            return "ABC"

    schema = strawberry.Schema(query=Query)

    expected_output = """
    directive @adminOrOwner on FIELD_DEFINITION

    type Query {
      name: String! @adminOrOwner
    }
    """
    assert print_schema(schema) == textwrap.dedent(expected_output).strip()

    result = schema.execute_sync("{ name }")

    assert result.errors is not None
    assert result.errors[0].message == "You need to be an admin or the owner"


@pytest.mark.asyncio
async def test_or_permission_for_subscription():
    class IsAdmin(BasePermission):
        message = "Not an admin"

        def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "admin"

    class IsOwner(BasePermission):
        message = "Not the owner"

        async def has_permission(self, source, info, **kwargs: typing.Any) -> bool:
            return info.context["role"] == "owner"

    @strawberry.type
    class Query:
        name: str = "Andrew"

    @strawberry.type
    class Subscription:
        @strawberry.subscription(
            extensions=[PermissionExtension([IsAdmin() | IsOwner()])]
        )
        async def user(self) -> typing.AsyncGenerator[str, None]:
            yield "Hello"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { user }"

    async with aclosing(
        await schema.subscribe(query, context_value={"role": "owner"})
    ) as sub_result:
        result = await sub_result.__anext__()

    assert result.errors is None
    assert result.data == {"user": "Hello"}

    async with aclosing(
        await schema.subscribe(query, context_value={"role": "guest"})
    ) as sub_result:
        result = await sub_result.__anext__()

    assert result.errors is not None
    assert result.errors[0].message == "Not an admin"


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


def test_sync_permission_returning_awaitable_denies_access():
    calls = 0

    class DenyViaAwaitable(BasePermission):
        message = "denied"

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> typing.Any:
            async def result() -> bool:
                return False

            return result()

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[DenyViaAwaitable])
        def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert "returned an awaitable" in result.errors[0].message
    assert calls == 0


@pytest.mark.asyncio
async def test_sync_permission_returning_awaitable_denies_access_on_async_execution():
    calls = 0

    class DenyViaAwaitable(BasePermission):
        message = "denied"

        def has_permission(
            self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
        ) -> typing.Any:
            async def result() -> bool:
                return False

            return result()

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[DenyViaAwaitable])
        def secret(self) -> str:
            nonlocal calls
            calls += 1
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = await schema.execute("{ secret }")

    assert result.data is None
    assert result.errors is not None
    assert "returned an awaitable" in result.errors[0].message
    assert calls == 0


class AsyncGeneratorPermission(BasePermission):
    async def has_permission(  # type: ignore[override]
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.AsyncGenerator[bool, None]:
        yield False  # pragma: no cover


class GeneratorPermission(BasePermission):
    def has_permission(  # type: ignore[override]
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Generator[bool, None, None]:
        yield False  # pragma: no cover


async def _async_generator() -> typing.AsyncGenerator[bool, None]:
    yield False  # pragma: no cover


class SyncReturningAsyncGeneratorPermission(BasePermission):
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        return _async_generator()


class AsyncReturningAsyncGeneratorPermission(BasePermission):
    async def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        return _async_generator()


class AsyncReturningCoroutinePermission(BasePermission):
    async def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        async def result() -> bool:
            return False  # pragma: no cover

        return result()


class TruthyPermission(BasePermission):
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        return "yes"


class AsyncTruthyPermission(BasePermission):
    async def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        return object()


class NonePermission(BasePermission):
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs: typing.Any
    ) -> typing.Any:
        return None


NON_BOOLEAN_PERMISSIONS = [
    pytest.param(AsyncGeneratorPermission, "async_generator", id="async-generator"),
    pytest.param(GeneratorPermission, "generator", id="generator"),
    pytest.param(
        SyncReturningAsyncGeneratorPermission,
        "async_generator",
        id="sync-returning-async-generator",
    ),
    pytest.param(TruthyPermission, "str", id="truthy"),
    pytest.param(NonePermission, "NoneType", id="none"),
]

ASYNC_ONLY_NON_BOOLEAN_PERMISSIONS = [
    pytest.param(
        AsyncReturningAsyncGeneratorPermission,
        "async_generator",
        id="async-returning-async-generator",
    ),
    pytest.param(
        AsyncReturningCoroutinePermission, "coroutine", id="async-returning-coroutine"
    ),
    pytest.param(AsyncTruthyPermission, "object", id="async-truthy"),
]


def _schema_with_permission(
    permission_class: type[BasePermission],
) -> tuple[strawberry.Schema, list[str]]:
    calls: list[str] = []

    @strawberry.type
    class Query:
        @strawberry.field(permission_classes=[permission_class])
        def secret(self) -> str | None:
            calls.append("query")
            return "secret"

        @strawberry.field(permission_classes=[permission_class])
        async def async_secret(self) -> str | None:
            calls.append("async query")
            return "secret"

    @strawberry.type
    class Mutation:
        @strawberry.mutation(permission_classes=[permission_class])
        def delete_everything(self) -> bool:
            calls.append("mutation")
            return True

        @strawberry.mutation(permission_classes=[permission_class])
        async def async_delete_everything(self) -> bool:
            calls.append("async mutation")
            return True

    return strawberry.Schema(query=Query, mutation=Mutation), calls


def _assert_rejected(
    result: ExecutionResult, calls: list[str], result_type: str
) -> None:
    assert result.errors is not None
    assert len(result.errors) == 1
    message = result.errors[0].message
    assert f"returned a value of type {result_type!r}" in message
    assert "permissions must return a boolean" in message
    assert ("must not use `yield`" in message) == ("generator" in result_type)
    assert calls == []


@pytest.mark.parametrize(("permission_class", "result_type"), NON_BOOLEAN_PERMISSIONS)
@pytest.mark.parametrize("query", ["{ secret }", "mutation { deleteEverything }"])
def test_permission_returning_non_boolean_denies_access(
    permission_class: type[BasePermission], result_type: str, query: str
):
    schema, calls = _schema_with_permission(permission_class)

    result = schema.execute_sync(query)

    _assert_rejected(result, calls, result_type)


@pytest.mark.parametrize(
    ("permission_class", "result_type"),
    NON_BOOLEAN_PERMISSIONS + ASYNC_ONLY_NON_BOOLEAN_PERMISSIONS,
)
@pytest.mark.parametrize(
    "query",
    [
        "{ secret }",
        "{ asyncSecret }",
        "mutation { deleteEverything }",
        "mutation { asyncDeleteEverything }",
    ],
)
async def test_permission_returning_non_boolean_denies_access_on_async_execution(
    permission_class: type[BasePermission], result_type: str, query: str
):
    schema, calls = _schema_with_permission(permission_class)

    result = await schema.execute(query)

    _assert_rejected(result, calls, result_type)


def test_permission_returning_non_boolean_is_not_silenced_by_fail_silently():
    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[
                PermissionExtension(
                    permissions=[TruthyPermission()], fail_silently=True
                )
            ]
        )
        def secret(self) -> str | None:  # pragma: no cover
            return "secret"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ secret }")

    assert result.errors is not None
    assert "permissions must return a boolean" in result.errors[0].message
