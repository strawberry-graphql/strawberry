"""Errors in the values sent by clients are `StrawberryInputCoercionError`s.

That lets error handling, like `MaskErrors`, tell them apart from server errors,
see docs/guides/errors.md.
"""

from graphql import GraphQLError

import strawberry
from strawberry.exceptions import StrawberryInputCoercionError
from strawberry.relay import GlobalID, GlobalIDValueError


def is_strawberry_input_error(error: GraphQLError) -> bool:
    # the check recommended by the docs
    return isinstance(error, StrawberryInputCoercionError) or isinstance(
        error.original_error, StrawberryInputCoercionError
    )


@strawberry.input
class UpdateInput:
    name: strawberry.Maybe[str]


@strawberry.type
class Query:
    @strawberry.field
    def update(self, input: UpdateInput) -> str:
        return "updated"

    @strawberry.field
    def rename(self, name: strawberry.Maybe[str]) -> str:
        return "renamed"

    @strawberry.field
    def node_type(self, id: GlobalID) -> str:
        return id.type_name


schema = strawberry.Schema(query=Query)


def test_null_for_a_maybe_input_field_in_the_query_is_an_input_error():
    result = schema.execute_sync("{ update(input: { name: null }) }")

    assert result.errors
    (error,) = result.errors
    assert is_strawberry_input_error(error)
    assert error.message.startswith("Expected value of type 'str', found null.")


def test_null_for_a_maybe_argument_in_the_query_is_an_input_error():
    result = schema.execute_sync("{ rename(name: null) }")

    assert result.errors
    (error,) = result.errors
    assert is_strawberry_input_error(error)
    assert "cannot be explicitly set to null" in error.message


def test_null_for_a_maybe_input_field_in_variables_is_an_input_error():
    result = schema.execute_sync(
        "query ($input: UpdateInput!) { update(input: $input) }",
        variable_values={"input": {"name": None}},
    )

    assert result.errors
    (error,) = result.errors
    assert is_strawberry_input_error(error)
    assert "cannot be explicitly set to null" in error.message


def test_invalid_global_id_is_an_input_error():
    result = schema.execute_sync('{ nodeType(id: "not a global id") }')

    assert result.errors
    (error,) = result.errors
    assert is_strawberry_input_error(error)
    # handlers of the previous error keep catching it
    assert isinstance(error.original_error, GlobalIDValueError)
    assert error.message == 'Value cannot represent a GlobalID: "not a global id".'
    assert error.path == ["nodeType"]


def test_valid_global_id_is_converted():
    global_id = str(GlobalID("Fruit", "1"))

    result = schema.execute_sync(f'{{ nodeType(id: "{global_id}") }}')

    assert not result.errors
    assert result.data == {"nodeType": "Fruit"}
