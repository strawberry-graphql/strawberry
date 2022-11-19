from enum import Enum

import pytest

import strawberry
from strawberry.exceptions import DuplicatedTypeName


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

    with pytest.raises(DuplicatedTypeName):
        strawberry.Schema(query=Query, types=[A, B])


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

    with pytest.raises(DuplicatedTypeName):
        strawberry.Schema(query=Query, types=[A, B])


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

    with pytest.raises(DuplicatedTypeName):
        strawberry.Schema(query=Query, types=[A, B])


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

    with pytest.raises(DuplicatedTypeName):
        strawberry.Schema(query=Query, types=[A, B])


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

    with pytest.raises(DuplicatedTypeName):
        strawberry.Schema(query=Query, types=[A, B])


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

    with pytest.raises(Exception) as exc_info:
        strawberry.Schema(query=Query, types=[B])

    assert isinstance(exc_info.value.__cause__, DuplicatedTypeName)
