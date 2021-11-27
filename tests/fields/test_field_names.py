"""These tests cover the functionality of StrawberryField names before they're added
to the Schema"""

import strawberry


def test_field_name_standard():
    standard_field = strawberry.field()

    assert standard_field.python_name is None
    assert standard_field.graphql_name is None


def test_field_name_override():
    field_name = "override"

    standard_field = strawberry.field(name=field_name)

    assert standard_field.python_name is None  # Set once field is added to a Schema
    assert standard_field.graphql_name == field_name
