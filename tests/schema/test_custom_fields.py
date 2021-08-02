import textwrap
from typing import Any, Dict, List, Optional, cast

import strawberry
from strawberry import StrawberryField


def test_simple_custom_field():
    class UpperCaseField(StrawberryField):
        def get_result(self, source: Any, info: Any, arguments: Dict[str, Any]) -> str:
            result = super().get_result(source, info, arguments)
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


def test_modify_arguments():
    class PageNumberPagination(StrawberryField):
        def get_result(
            self, source: Any, info: Any, arguments: Dict[str, Any]
        ) -> List[Any]:
            first = arguments.pop("first", None)
            result = super().get_result(source, info, arguments)

            # We're going to assume that the resolver returns the right thing
            # here
            result = cast(List[Any], result)

            if first is not None:
                return result[:first]
            return result

        def get_arguments(self) -> Dict[str, object]:
            arguments = super().get_arguments()
            arguments["first"] = Optional[int]

            return arguments

    @strawberry.type
    class Query:
        @PageNumberPagination()
        def books(self) -> List[str]:
            return [
                "Pride and Prejudice",
                "Sense and Sensibility",
                "Persuasion",
                "Mansfield Park",
            ]

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent(
        """
        type Query {
          books(first: Int): [String!]!
        }
        """
    ).strip()

    assert str(schema) == expected

    result = schema.execute_sync("{ books(first: 2) }")

    assert not result.errors
    assert result.data["books"] == ["Pride and Prejudice", "Sense and Sensibility"]


def test_modify_arguments_with_default():
    class PageNumberPagination(StrawberryField):
        def get_result(
            self, source: Any, info: Any, arguments: Dict[str, Any]
        ) -> List[Any]:
            first = arguments.pop("first", None)
            result = super().get_result(source, info, arguments)

            # We're going to assume that the resolver returns the right thing
            # here
            result = cast(List[Any], result)

            if first is not None:
                return result[:first]
            return result

        def get_arguments(self) -> Dict[str, object]:
            arguments = super().get_arguments()
            arguments["first"] = self.create_argument(type_annotation=int, default=2)

            return arguments

    @strawberry.type
    class Query:
        @PageNumberPagination()
        def books(self) -> List[str]:
            return [
                "Pride and Prejudice",
                "Sense and Sensibility",
                "Persuasion",
                "Mansfield Park",
            ]

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent(
        """
        type Query {
          books(first: Int! = 2): [String!]!
        }
        """
    ).strip()

    assert str(schema) == expected

    result = schema.execute_sync("{ books }")

    assert not result.errors
    assert result.data["books"] == ["Pride and Prejudice", "Sense and Sensibility"]


def test_modify_return_type():
    class AuthenticationRequired(StrawberryField):
        def get_type(self) -> object:
            type_ = super().get_type()
            return Optional[type_]

        def get_result(self, source, info, arguments):
            if not info.context["is_authenticated"]:
                return None

            return super().get_result(source, info, arguments)

    @strawberry.type
    class Query:
        name: str = AuthenticationRequired(default="Patrick")

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent(
        """
        type Query {
          name: String
        }
        """
    ).strip()

    assert str(schema) == expected

    result = schema.execute_sync(
        "{ name }",
        root_value=Query(),
        context_value={"is_authenticated": False},
    )

    assert not result.errors
    assert result.data["name"] is None

    result = schema.execute_sync(
        "{ name }",
        root_value=Query(),
        context_value={"is_authenticated": True},
    )

    assert not result.errors
    assert result.data["name"] == "Patrick"
