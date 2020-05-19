import pytest

import strawberry
from graphql import (
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLNonNull,
    GraphQLScalarType,
    Undefined,
)
from strawberry.exceptions import (
    MissingArgumentsAnnotationsError,
    MissingReturnAnnotationError,
)


def test_field_as_function():
    field: str = strawberry.field()

    assert field.field_description is None


def test_field_arguments():
    @strawberry.field
    def hello(self, info, id: int) -> str:
        return "I'm a resolver"

    assert hello.graphql_type

    assert type(hello.graphql_type) == GraphQLField
    assert type(hello.graphql_type.type) == GraphQLNonNull
    assert hello.graphql_type.type.of_type.name == "String"

    assert type(hello.graphql_type.args["id"].type) == GraphQLNonNull
    assert hello.graphql_type.args["id"].type.of_type.name == "Int"


def test_field_default_arguments_are_optional():
    @strawberry.field
    def hello(self, info, test: int, id: int = 1, asdf: str = None) -> str:
        return "I'm a resolver"

    assert hello.graphql_type

    assert type(hello.graphql_type) == GraphQLField
    assert type(hello.graphql_type.type) == GraphQLNonNull
    assert hello.graphql_type.type.of_type.name == "String"

    assert type(hello.graphql_type.args["id"].type) == GraphQLNonNull
    assert hello.graphql_type.args["id"].type.of_type.name == "Int"
    assert hello.graphql_type.args["id"].default_value == 1

    assert type(hello.graphql_type.args["asdf"].type) == GraphQLScalarType
    assert hello.graphql_type.args["asdf"].type.name == "String"
    assert hello.graphql_type.args["asdf"].default_value == Undefined


def test_field_default_optional_argument_custom_type():
    @strawberry.input
    class CustomInputType:
        field: str

    @strawberry.field
    def hello(
        self, info, required: CustomInputType, optional: CustomInputType = None
    ) -> str:
        return "I'm a resolver"

    assert hello.graphql_type

    assert type(hello.graphql_type) == GraphQLField
    assert type(hello.graphql_type.type) == GraphQLNonNull
    assert hello.graphql_type.type.of_type.name == "String"

    assert type(hello.graphql_type.args["required"].type) == GraphQLNonNull
    assert hello.graphql_type.args["required"].type.of_type.name == "CustomInputType"
    assert hello.graphql_type.args["required"].default_value == Undefined

    assert type(hello.graphql_type.args["optional"].type) == GraphQLInputObjectType
    assert hello.graphql_type.args["optional"].type.name == "CustomInputType"
    assert hello.graphql_type.args["optional"].default_value == Undefined


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
