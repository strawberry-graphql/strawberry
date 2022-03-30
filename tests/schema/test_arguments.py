import datetime
from textwrap import dedent
from typing import List, Optional, Tuple

import pytest

from typing_extensions import Annotated

import strawberry
from strawberry.arguments import UNSET, is_unset
from strawberry.schema.config import StrawberryConfig
from strawberry.types.info import Info


def test_argument_descriptions():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(description="Your name")  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        type Query {
          hello(
            """Your name"""
            name: String! = "Patrick"
          ): String!
        }'''
    )


def test_argument_deprecation_reason():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(deprecation_reason="Your reason")  # noqa: F722
            ] = "Patrick"
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String! = "Patrick" @deprecated(reason: "Your reason")): String!
        }"""
    )


def test_argument_names():
    @strawberry.input
    class HelloInput:
        name: str = strawberry.field(default="Patrick", description="Your name")

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self, input_: Annotated[HelloInput, strawberry.argument(name="input")]
        ) -> str:
            return f"Hi {input_.name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        input HelloInput {
          """Your name"""
          name: String! = "Patrick"
        }

        type Query {
          hello(input: HelloInput!): String!
        }'''
    )


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = None) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String = null): String!
        }"""
    )


def test_optional_argument_unset():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = UNSET, age: Optional[int] = UNSET) -> str:
            if is_unset(name):
                return "Hi there"
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String, age: Int): String!
        }"""
    )

    result = schema.execute_sync(
        """
        query {
            hello
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}


def test_optional_input_field_unset():
    @strawberry.input
    class TestInput:
        name: Optional[str] = UNSET
        age: Optional[int] = UNSET

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, input: TestInput) -> str:
            if is_unset(input.name):
                return "Hi there"
            return f"Hi {input.name}"

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
        type Query {
          hello(input: TestInput!): String!
        }

        input TestInput {
          name: String
          age: Int
        }
        """
        ).strip()
    )

    result = schema.execute_sync(
        """
        query {
            hello(input: {})
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}


@pytest.mark.parametrize(
    "query",
    [
        (
            """
            query {
                typenames(date: "2022-02-22") {
                    arg
                    info
                }
            }
            """,
            None,
        ),
        (
            """
            query($date: Date!) {
                typenames(date: $date) {
                    arg
                    info
                }
            }
            """,
            {"date": "2022-02-22"},
        ),
    ],
    ids=["argument", "variable"],
)
def test_argument_type_date(query: List[Tuple[str, Optional[dict]]]):
    """
    Ensure that accessing a date both via resolver argument and
    `Info` dictionary gives a `date` object. Also make sure that
    it makes no difference if passing that value directly as
    part of the `query` or using the `variable_values` dictionary.
    """
    import datetime

    @strawberry.type
    class TypeNames:
        arg: str
        info: str

    @strawberry.type
    class Query:
        @strawberry.field
        def typenames(self, info: Info, date: datetime.date) -> TypeNames:
            [selected_field] = info.selected_fields
            return TypeNames(
                arg=type(date).__name__,
                info=type(selected_field.arguments["date"]).__name__,
            )

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(*query)
    assert not result.errors
    assert result.data["typenames"]["arg"] == "date"
    assert result.data["typenames"]["info"] == "date"


@pytest.mark.parametrize(
    "query",
    [
        (
            """
            query {
                typenames(obj: { date: "2022-02-22" }) {
                    obj
                    obj__date
                    info__obj
                    info__obj__date
                }
            }
            """,
            None,
        ),
        (
            """
            query($obj: Obj!) {
                typenames(obj: $obj) {
                    obj
                    obj__date
                    info__obj
                    info__obj__date
                }
            }
            """,
            {"obj": {"date": "2022-02-22"}},
        ),
    ],
    ids=["argument", "variable"],
)
def test_argument_type_dataclass(query: List[Tuple[str, Optional[dict]]]):
    """
    Ensure that accessing a dataclass both via resolver argument and
    `Info` dictionary gives the proper object. Also make sure that
    it makes no difference if passing that value directly as
    part of the `query` or using the `variable_values` dictionary.
    """

    @strawberry.input
    class Obj:
        date: Optional[datetime.date] = None

    @strawberry.type
    class TypeNames:
        obj: str
        obj__date: str
        info__obj: str
        info__obj__date: str

    @strawberry.type
    class Query:
        @strawberry.field
        def typenames(self, info: Info, obj: Optional[Obj] = None) -> TypeNames:
            [field] = info.selected_fields
            info__obj = field.arguments["obj"]
            info__obj__date = (
                info__obj.date if isinstance(info__obj, Obj) else info__obj["date"]
            )
            return TypeNames(
                obj=type(obj).__name__,
                obj__date=type(obj.date).__name__,
                info__obj=type(info__obj).__name__,
                info__obj__date=type(info__obj__date).__name__,
            )

    config = StrawberryConfig(auto_camel_case=False)
    schema = strawberry.Schema(query=Query, config=config)

    result = schema.execute_sync(*query)

    assert not result.errors
    assert result.data["typenames"]["obj"] == "Obj"
    assert result.data["typenames"]["obj__date"] == "date"
    assert result.data["typenames"]["info__obj"] == "Obj"
    assert result.data["typenames"]["info__obj__date"] == "date"
