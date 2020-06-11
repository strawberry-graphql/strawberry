from typing import List, Optional, Union

import pytest

import strawberry


def test_unions():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Query:
        user: Union[User, Error]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"

    union_type_definition = definition.fields[0].type._union_definition

    assert union_type_definition.name == "UserError"
    assert union_type_definition.types == (User, Error)


def test_unions_inside_optional():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Query:
        user: Optional[Union[User, Error]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].is_optional

    union_type_definition = definition.fields[0].type._union_definition

    assert union_type_definition.name == "UserError"
    assert union_type_definition.types == (User, Error)


def test_unions_inside_list():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Query:
        user: List[Union[User, Error]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "user"
    assert definition.fields[0].is_list

    union_type_definition = definition.fields[0].child.type._union_definition

    assert union_type_definition.name == "UserError"
    assert union_type_definition.types == (User, Error)


def test_cannot_use_union_directly():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    with pytest.raises(ValueError, match=r"Cannot use union type directly"):
        Result()
