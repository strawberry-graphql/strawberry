import strawberry


def test_field_name_standard():
    standard_field = strawberry.field()

    assert standard_field.python_name is None
    assert standard_field.graphql_name is None


def test_field_name_standard_on_schema():
    @strawberry.type()
    class Query:
        normal_field: int

    [field] = Query.__strawberry_definition__.fields

    assert field.python_name == "normal_field"
    assert field.graphql_name is None


def test_field_name_override():
    field_name = "override"

    standard_field = strawberry.field(name=field_name)

    assert standard_field.python_name is None  # Set once field is added to a Schema
    assert standard_field.graphql_name == field_name


def test_field_name_override_with_schema():
    field_name = "override_name"

    @strawberry.type()
    class Query:
        override_field: bool = strawberry.field(name=field_name)

    [field] = Query.__strawberry_definition__.fields

    assert field.python_name == "override_field"
    assert field.graphql_name == field_name
