from textwrap import dedent
from typing import Any, Awaitable, Dict, Type, Union, cast, List

import strawberry
from strawberry.field import StrawberryField
from strawberry.arguments import StrawberryArgument, UNSET
from strawberry.types.generics import get_name_from_types


def test_simple_custom_field():
    class UpperCaseField(StrawberryField):
        def get_result(
            self, kwargs: Dict[str, Any], source: Any, info: Any
        ) -> Union[Awaitable[Any], Any]:
            result = super().get_result(kwargs, source, info)
            return cast(str, result).upper()

    @strawberry.type
    class Query:
        name: str = UpperCaseField(default="Patrick")

        @UpperCaseField()
        def alt_name() -> str:
            return "patrick91"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ name, altName }", root_value=Query())

    assert not result.errors
    assert result.data["name"] == "PATRICK"
    assert result.data["altName"] == "PATRICK91"


def test_modify_return_type():
    class AuthenticationRequired(StrawberryField):
        def get_result(
            self, kwargs: Dict[str, Any], source: Any, info: Any
        ) -> Union[Awaitable[Any], Any]:
            if not info.context["is_authenticated"]:
                return None

            return super().get_result(kwargs, source, info)

        def get_type(self) -> Type:
            self.is_optional = True
            return self.type

    @strawberry.type
    class Query:
        name: str = AuthenticationRequired(default="Patrick")

        @AuthenticationRequired()
        def alt_name() -> str:
            return "patrick91"

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
            type Query {
              name: String
              altName: String
            }
            """
        ).strip()
    )

    result = schema.execute_sync(
        "{ name, altName }",
        root_value=Query(),
        context_value={"is_authenticated": False},
    )

    assert not result.errors
    assert result.data["name"] is None
    assert result.data["altName"] is None

    result = schema.execute_sync(
        "{ name, altName }",
        root_value=Query(),
        context_value={"is_authenticated": True},
    )

    assert not result.errors
    assert result.data["name"] == "Patrick"
    assert result.data["altName"] == "patrick91"


def test_arguments():
    class Paginated(StrawberryField):
        def get_result(
            self, kwargs: Dict[str, Any], source: Any, info: Any
        ) -> Union[Awaitable[Any], Any]:
            first = kwargs.pop("first", None)
            result = super().get_result(kwargs, source, info)

            if first is not None:
                return result[:first]
            return result

        @property
        def arguments(self) -> List[StrawberryArgument]:
            arguments = super().arguments
            first_arg = StrawberryArgument(
                type_=int,
                python_name="first",
                graphql_name="first",
                default_value=UNSET,
                description=None,
                origin=None,
            )
            return arguments + [first_arg]

    @strawberry.type
    class Query:
        @Paginated()
        def books() -> List[str]:
            return [
                "Pride and Prejudice",
                "Sense and Sensibility",
                "Persuasion",
                "Mansfield Park",
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ books(first: 2) }")

    assert not result.errors
    assert result.data["books"] == ["Pride and Prejudice", "Sense and Sensibility"]


def test_return_union():
    @strawberry.type
    class PermissionDeniedError:
        message: str = "Permission denied"

    class AnonymousReturn(StrawberryField):
        def __init__(self, *args, value, **kwargs):
            super().__init__(*args, **kwargs)
            self.value = value

        def get_result(
            self, kwargs: Dict[str, Any], source: Any, info: Any
        ) -> Union[Awaitable[Any], Any]:
            if not info.context["is_authenticated"]:
                if callable(self.value):
                    return self.value()
                return self.value

            return super().get_result(kwargs, source, info)

        def get_type(self) -> Type:
            if self.value is not None:
                types = (self.type, self.value)
                self.is_union = True
                return strawberry.union(
                    get_name_from_types(types), types=types
                )

            if self.value is None:
                self.is_optional = True

            return self.type

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @AnonymousReturn(value=PermissionDeniedError)
        def user() -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ user { __typename } }",
        context_value={"is_authenticated": False}
    )

    assert not result.errors
    assert result.data["user"] == {
        "__typename": "PermissionDeniedError",
    }

    result = schema.execute_sync(
        "{ user { __typename } }",
        context_value={"is_authenticated": True}
    )

    assert not result.errors
    assert result.data["user"] == {
        "__typename": "User",
    }
