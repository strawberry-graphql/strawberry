from typing import Optional

import strawberry
from strawberry.type import StrawberryOptional


def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: Optional[str]
        age: Optional[int]

    definition = Query._type_definition
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: Optional[str] = strawberry.field(name="name")
        y: Optional[int] = strawberry.field(name="age")

    definition = Query._type_definition
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: Optional[str] = strawberry.field()
        age: Optional[int] = strawberry.field()

    definition = Query._type_definition
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


def test_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> Optional[str]:
            return "Name"

    definition = Query._type_definition
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "name"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is str


def test_resolver_fields_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> Optional[str]:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "name"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is str

    [argument] = field.arguments

    assert argument.graphql_name == "argument"
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str
