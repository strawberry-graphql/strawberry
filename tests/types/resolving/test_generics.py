from enum import Enum
from typing import Generic, List, Optional, TypeVar, Union

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.enum import EnumDefinition
from strawberry.field import StrawberryField
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryTypeVar
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


def test_basic_generic():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(T)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryTypeVar)
    assert resolved.is_generic
    assert resolved.type_var is T

    assert resolved == T


def test_generic_lists():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(List[T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert isinstance(resolved.of_type, StrawberryTypeVar)
    assert resolved.is_generic

    assert resolved == List[T]


def test_generic_objects():
    T = TypeVar("T")

    @strawberry.type
    class FooBar(Generic[T]):
        thing: T

    annotation = StrawberryAnnotation(FooBar)
    resolved = annotation.resolve()

    # TODO: Simplify with StrawberryObject
    assert isinstance(resolved, type)
    assert hasattr(resolved, "_type_definition")
    assert isinstance(resolved._type_definition, TypeDefinition)
    assert resolved._type_definition.is_generic

    field: StrawberryField = resolved._type_definition.fields[0]
    assert isinstance(field.type, StrawberryTypeVar)
    assert field.type == T


def test_generic_optionals():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(Optional[T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert isinstance(resolved.of_type, StrawberryTypeVar)
    assert resolved.is_generic

    assert resolved == Optional[T]


def test_generic_unions():
    S = TypeVar("S")
    T = TypeVar("T")

    annotation = StrawberryAnnotation(Union[S, T])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.types == (S, T)
    assert resolved.is_generic

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
    assert hasattr(resolved, "_type_definition")
    assert isinstance(resolved._type_definition, TypeDefinition)

    generic_slot_field: StrawberryField = resolved._type_definition.fields[0]
    assert isinstance(generic_slot_field.type, EnumDefinition)
    assert generic_slot_field.type is VehicleMake._enum_definition
