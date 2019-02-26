from graphql import GraphQLField, GraphQLNonNull

import strawberry


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
