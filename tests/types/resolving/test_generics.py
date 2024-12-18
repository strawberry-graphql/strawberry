from enum import Enum
from typing import Generic, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import (
    StrawberryList,
    StrawberryObjectDefinition,
    StrawberryOptional,
    StrawberryTypeVar,
    get_object_definition,
    has_object_definition,
)
from strawberry.types.enum import EnumDefinition
from strawberry.types.field import StrawberryField
from strawberry.types.union import StrawberryUnion


def test_basic_generic():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(T)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryTypeVar)
    assert resolved.is_graphql_generic
    assert resolved.type_var is T

    assert resolved == T


def test_generic_lists():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(list[T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert isinstance(resolved.of_type, StrawberryTypeVar)
    assert resolved.is_graphql_generic

    assert resolved == list[T]


def test_generic_objects():
    T = TypeVar("T")

    @strawberry.type
    class FooBar(Generic[T]):
        thing: T

    annotation = StrawberryAnnotation(FooBar)
    resolved = annotation.resolve()

    # TODO: Simplify with StrawberryObject
    assert isinstance(resolved, type)
    assert has_object_definition(resolved)
    assert isinstance(resolved.__strawberry_definition__, StrawberryObjectDefinition)
    assert resolved.__strawberry_definition__.is_graphql_generic

    field: StrawberryField = resolved.__strawberry_definition__.fields[0]
    assert isinstance(field.type, StrawberryTypeVar)
    assert field.type == T


def test_generic_optionals():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(Optional[T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert isinstance(resolved.of_type, StrawberryTypeVar)
    assert resolved.is_graphql_generic

    assert resolved == Optional[T]


def test_generic_unions():
    S = TypeVar("S")
    T = TypeVar("T")

    annotation = StrawberryAnnotation(Union[S, T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.types == (S, T)
    assert resolved.is_graphql_generic

    assert resolved == Union[S, T]


def test_generic_with_enums():
    T = TypeVar("T")

    @strawberry.enum
    class VehicleMake(Enum):
        FORD = "ford"
        TOYOTA = "toyota"
        HONDA = "honda"

    @strawberry.type
    class GenericForEnum(Generic[T]):
        generic_slot: T

    annotation = StrawberryAnnotation(GenericForEnum[VehicleMake])
    resolved = annotation.resolve()

    # TODO: Simplify with StrawberryObject
    assert isinstance(resolved, type)
    assert has_object_definition(resolved)
    assert isinstance(resolved.__strawberry_definition__, StrawberryObjectDefinition)

    generic_slot_field: StrawberryField = resolved.__strawberry_definition__.fields[0]
    assert isinstance(generic_slot_field.type, EnumDefinition)
    assert generic_slot_field.type is VehicleMake._enum_definition


def test_cant_create_concrete_of_non_strawberry_object():
    T = TypeVar("T")

    @strawberry.type
    class Foo(Generic[T]):
        generic_slot: T

    with pytest.raises(ValueError):
        StrawberryAnnotation(Foo).create_concrete_type(int)


def test_inline_resolver():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        @strawberry.field
        def node(self) -> T:  # type: ignore  # pragma: no cover
            ...

    resolved = StrawberryAnnotation(Edge).resolve()

    type_definition = get_object_definition(resolved, strict=True)

    assert type_definition.is_graphql_generic
