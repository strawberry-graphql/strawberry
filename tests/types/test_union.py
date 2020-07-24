from typing import Generic, List, Optional, TypeVar, Union

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


def test_named_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    union_type_definition = Result._union_definition

    assert union_type_definition.name == "Result"
    assert union_type_definition.types == (A, B)


def test_union_with_generic():
    T = TypeVar("T")

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    Result = strawberry.union("Result", (Error, Edge[str]))

    union_type_definition = Result._union_definition

    assert union_type_definition.name == "Result"
    assert union_type_definition.types[0] == Error

    assert union_type_definition.types[1]._type_definition.is_generic is False
    assert union_type_definition.types[1]._type_definition.name == "StrEdge"


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
