from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import InvalidUnionType
from strawberry.type import StrawberryOptional, StrawberryList
from strawberry.union import StrawberryUnion


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

    assert definition.fields[0].graphql_name == "user"

    union_type_definition = definition.fields[0].type
    assert isinstance(union_type_definition, StrawberryUnion)
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

    assert definition.fields[0].graphql_name == "user"
    assert isinstance(definition.fields[0].type, StrawberryOptional)

    strawberry_union = definition.fields[0].type.of_type
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.name == "UserError"
    assert strawberry_union.types == (User, Error)


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

    assert definition.fields[0].graphql_name == "user"
    assert isinstance(definition.fields[0].type, StrawberryList)

    strawberry_union = definition.fields[0].type.of_type
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.name == "UserError"
    assert strawberry_union.types == (User, Error)


def test_named_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.name == "Result"
    assert strawberry_union.types == (A, B)


def test_union_with_generic():
    T = TypeVar("T")

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    Result = strawberry.union("Result", (Error, Edge[str]))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.name == "Result"
    assert strawberry_union.types[0] == Error

    assert strawberry_union.types[1]._type_definition.is_generic is False
    assert strawberry_union.types[1]._type_definition.name == "StrEdge"


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


def test_error_with_empty_type_list():
    with pytest.raises(TypeError, match="No types passed to `union`"):
        strawberry.union("Result", [])


def test_error_with_scalar_types():
    with pytest.raises(
        InvalidUnionType, match="Scalar type `int` cannot be used in a GraphQL Union"
    ):
        strawberry.union("Result", (int,))


def test_error_with_non_strawberry_type():
    @dataclass
    class A:
        a: int

    with pytest.raises(
        InvalidUnionType, match="Union type `A` is not a Strawberry type"
    ):
        strawberry.union("Result", (A,))
