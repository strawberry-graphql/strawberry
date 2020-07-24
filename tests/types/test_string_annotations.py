# type: ignore

from typing import List, Optional

import strawberry


def test_basic_types():
    @strawberry.type
    class Query:
        name: "str"
        age: "int"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int


def test_optional():
    @strawberry.type
    class Query:
        name: "Optional[str]"
        age: "Optional[int]"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].type == str
    assert definition.fields[0].is_optional

    assert definition.fields[1].name == "age"
    assert definition.fields[1].type == int
    assert definition.fields[1].is_optional


def test_basic_list():
    @strawberry.type
    class Query:
        names: "List[str]"

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False


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
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "users"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == User
    assert definition.fields[0].child.is_optional is False

    del User
