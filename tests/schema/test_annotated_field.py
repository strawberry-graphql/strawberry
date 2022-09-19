import textwrap
from typing import Generic, Optional, TypeVar

from typing_extensions import Annotated

import strawberry
from strawberry.private import Private
from strawberry.type import StrawberryAnnotated, StrawberryOptional
from strawberry.types.types import TypeDefinition


def test_annotated_field():
    GenericType = TypeVar("GenericType")

    @strawberry.type
    class GenericData(Generic[GenericType]):
        value: GenericType

    @strawberry.type
    class Query:
        name: Annotated[Optional[str], "string"]
        age: Annotated[int, "number"]
        private_number: Annotated[Private[int], "private number"]
        generic: Annotated[GenericData[int], "generic int"]

        @strawberry.field
        def resolver(self, arg: Annotated[str, "arg"]) -> Annotated[str, "return"]:
            return f"arg={arg}"

    definition: TypeDefinition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 4

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == StrawberryAnnotated(
        StrawberryOptional(str), "string"
    )

    assert definition.fields[1].python_name == "age"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type == StrawberryAnnotated(int, "number")

    assert definition.fields[2].python_name == "generic"
    assert definition.fields[2].graphql_name is None
    generic_type, generic_args = StrawberryAnnotated.get_type_and_args(
        definition.fields[2].type
    )
    assert (
        generic_type.__name__ == "GenericData"
    )  # Strawberry auto-generates generic classes, cannot be compared directly
    assert generic_args == ("generic int",)

    assert definition.fields[3].python_name == "resolver"
    assert definition.fields[3].graphql_name is None
    assert definition.fields[3].type == StrawberryAnnotated(str, "return")

    assert len(definition.fields[3].arguments) == 1
    assert definition.fields[3].arguments[0].python_name == "arg"
    assert definition.fields[3].arguments[0].graphql_name is None
    assert definition.fields[3].arguments[0].type == StrawberryAnnotated(str, "arg")

    schema = strawberry.Schema(query=Query)
    expected = """
        type IntGenericData {
          value: Int!
        }

        type Query {
          name: String
          age: Int!
          generic: IntGenericData!
          resolver(arg: String!): String!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()

    query = """{
        name
        age
        generic {
          value
        }
        resolver(arg: "test")
    }"""
    result = schema.execute_sync(
        query,
        root_value=Query(
            name="name",
            age=123,
            private_number=56,
            generic=GenericData[int](value=1234),
        ),
    )
    assert not result.errors
    assert result.data == {
        "name": "name",
        "age": 123,
        "generic": {"value": 1234},
        "resolver": "arg=test",
    }
