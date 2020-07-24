from typing import Optional

import strawberry


def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: Optional[str]
        age: Optional[int]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int
    assert definition.fields[1].is_optional


def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: Optional[str] = strawberry.field(name="name")
        y: Optional[int] = strawberry.field(name="age")

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int
    assert definition.fields[1].is_optional


def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: Optional[str] = strawberry.field()
        age: Optional[int] = strawberry.field()

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int
    assert definition.fields[1].is_optional


def test_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> Optional[str]:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional


def test_resolver_fields_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> Optional[str]:
            return "Name"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert len(definition.fields[0].arguments) == 1
    assert definition.fields[0].arguments[0].name == "argument"
    assert definition.fields[0].arguments[0].type == str
    assert definition.fields[0].arguments[0].is_optional
