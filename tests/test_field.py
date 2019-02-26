import pytest
from graphql import GraphQLField, GraphQLNonNull

import strawberry
from strawberry.exceptions import MissingReturnAnnotationError


def test_field_arguments():
    @strawberry.field
    def hello(self, root, info, id: int) -> str:
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
