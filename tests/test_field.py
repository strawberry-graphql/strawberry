import pytest

import strawberry
from graphql import GraphQLField, GraphQLNonNull, graphql_sync
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingReturnAnnotationError,
)


def test_field_as_function():
    field: str = strawberry.field()

    assert field.description is None


def test_field_arguments():
    @strawberry.field
    def hello(self, info, id: int) -> str:
        return "I'm a resolver"

    assert hello.field

    assert type(hello.field) == GraphQLField
    assert type(hello.field.type) == GraphQLNonNull
    assert hello.field.type.of_type.name == "String"

    assert type(hello.field.args["id"].type) == GraphQLNonNull
    assert hello.field.args["id"].type.of_type.name == "Int"


def test_raises_error_when_return_annotation_missing():
    with pytest.raises(MissingReturnAnnotationError) as e:

        @strawberry.field
        def hello(self, info):
            return "I'm a resolver"

    assert e.value.args == (
        'Return annotation missing for field "hello", did you forget to add it?',
    )


def test_raises_error_when_argument_annotation_missing():
    with pytest.raises(MissingArgumentsAnnotationsError) as e:

        @strawberry.field
        def hello(self, info, query) -> str:
            return "I'm a resolver"

    assert e.value.args == (
        'Missing annotation for argument "query" in field "hello", '
        "did you forget to add it?",
    )

    with pytest.raises(MissingArgumentsAnnotationsError) as e:

        @strawberry.field
        def hello2(self, info, query, limit) -> str:
            return "I'm a resolver"

    assert e.value.args == (
        'Missing annotation for arguments "limit" and "query" '
        'in field "hello2", did you forget to add it?',
    )


def test_stores_description():
    @strawberry.type
    class Query:
        a: str = strawberry.field(description="Example")

        @strawberry.field
        def b(self, info, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field(description="Example C")
        def c(self, info, id: int) -> str:
            return "I'm a resolver"

        @strawberry.field
        def d(self, info, id: int) -> str:
            """Example D"""
            return "I'm a resolver"

        @strawberry.field(description="Inline description")
        def e(self, info, id: int) -> str:
            """Doc string description"""
            return "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Query") {
            fields {
                name
                description
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors

    assert result.data["__type"]["fields"] == [
        {"name": "a", "description": "Example"},
        {"name": "b", "description": None},
        {"name": "c", "description": "Example C"},
        {"name": "d", "description": "Example D"},
        {"name": "e", "description": "Inline description"},
    ]
