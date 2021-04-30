from typing import List, Optional

import strawberry
from strawberry.type import StrawberryOptional, StrawberryList


def test_basic_types():
    @strawberry.type
    class Query:
        name: "str"
        age: "int"

    definition = Query._type_definition
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert field1.type is str

    assert field2.graphql_name == "age"
    assert field2.type is int


def test_optional():
    @strawberry.type
    class Query:
        name: "Optional[str]"
        age: "Optional[int]"

    definition = Query._type_definition
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


def test_basic_list():
    @strawberry.type
    class Query:
        names: "List[str]"

    definition = Query._type_definition
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is str


def test_list_of_types():
    global User

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        users: "List[User]"

    definition = Query._type_definition
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "users"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is User

    del User
