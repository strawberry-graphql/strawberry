import textwrap
from enum import Enum
from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.exceptions import DuplicatedTypeName


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_input_types():
    @strawberry.input(name="DuplicatedInput")
    class A:
        a: int

    @strawberry.input(name="DuplicatedInput")
    class B:
        b: int

    @strawberry.type
    class Query:
        field: int

    strawberry.Schema(query=Query, types=[A, B])


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_types():
    @strawberry.type(name="DuplicatedType")
    class A:
        a: int

    @strawberry.type(name="DuplicatedType")
    class B:
        b: int

    @strawberry.type
    class Query:
        field: int

    strawberry.Schema(query=Query, types=[A, B])


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_interfaces():
    @strawberry.interface(name="DuplicatedType")
    class A:
        a: int

    @strawberry.interface(name="DuplicatedType")
    class B:
        b: int

    @strawberry.type
    class Query:
        pass

    strawberry.Schema(query=Query, types=[A, B])


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_enums():
    @strawberry.enum(name="DuplicatedType")
    class A(Enum):
        A = 1

    @strawberry.enum(name="DuplicatedType")
    class B(Enum):
        B = 1

    @strawberry.type
    class Query:
        field: int

    strawberry.Schema(query=Query, types=[A, B])


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_names_across_different_types():
    @strawberry.interface(name="DuplicatedType")
    class A:
        a: int

    @strawberry.type(name="DuplicatedType")
    class B:
        b: int

    @strawberry.type
    class Query:
        field: int

    strawberry.Schema(query=Query, types=[A, B])


@pytest.mark.raises_strawberry_exception(
    DuplicatedTypeName,
    match=r"Type (.*) is defined multiple times in the schema",
)
def test_schema_has_no_duplicated_types_between_schema_and_extra_types():
    @strawberry.type(name="DuplicatedType")
    class A:
        a: int

    @strawberry.type(name="DuplicatedType")
    class B:
        b: int

    @strawberry.type
    class Query:
        field: A

    strawberry.Schema(query=Query, types=[B])


def test_allows_multiple_instance_of_same_generic():
    T = TypeVar("T")

    @strawberry.type
    class A(Generic[T]):
        a: T

    @strawberry.type
    class Query:
        first: A[int]
        second: A[int]

    schema = strawberry.Schema(Query)

    expected_schema = textwrap.dedent(
        """
        type IntA {
          a: Int!
        }

        type Query {
          first: IntA!
          second: IntA!
        }
        """
    ).strip()

    assert str(schema) == expected_schema
