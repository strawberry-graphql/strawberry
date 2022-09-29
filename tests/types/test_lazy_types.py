# type: ignore
import enum
from typing import Generic, TypeVar

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField
from strawberry.lazy_type import LazyType
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.types import TypeDefinition


# This type is in the same file but should adequately test the logic.
@strawberry.type
class LaziestType:
    something: bool


@strawberry.enum
class LazyEnum(enum.Enum):
    BREAD = "BREAD"


def test_lazy_type():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved is LazierType
    assert resolved.resolve_type() is LaziestType


def test_lazy_type_enum():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LazyEnum", "test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved is LazierType
    assert resolved.resolve_type() is LazyEnum


def test_lazy_type_argument():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")

    @strawberry.mutation
    def slack_off(emotion: LazierType) -> bool:
        _ = emotion
        return True

    argument = slack_off.arguments[0]
    assert isinstance(argument.type, LazyType)
    assert argument.type is LazierType
    assert argument.type.resolve_type() is LaziestType


def test_lazy_type_field():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    field = StrawberryField(type_annotation=annotation)

    assert isinstance(field.type, LazyType)
    assert field.type is LazierType
    assert field.type.resolve_type() is LaziestType


def test_lazy_type_generic():
    T = TypeVar("T")

    @strawberry.type
    class GenericType(Generic[T]):
        item: T

    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")
    ResolvedType = GenericType[LazierType]

    annotation = StrawberryAnnotation(ResolvedType)
    resolved = annotation.resolve()

    # TODO: Simplify with StrawberryObject
    assert isinstance(resolved, type)
    assert hasattr(resolved, "_type_definition")
    assert isinstance(resolved._type_definition, TypeDefinition)

    items_field: StrawberryField = resolved._type_definition.fields[0]
    assert items_field.type is LazierType
    assert items_field.type.resolve_type() is LaziestType


def test_lazy_type_object():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")

    @strawberry.type
    class WaterParkFeature:
        river: LazierType

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = WaterParkFeature._type_definition.fields[0]

    assert isinstance(field.type, LazyType)
    assert field.type is LazierType
    assert field.type.resolve_type() is LaziestType


def test_lazy_type_resolver():
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType("LaziestType", "test_lazy_types")

    def slaking_pokemon() -> LazierType:
        raise NotImplementedError

    resolver = StrawberryResolver(slaking_pokemon)
    assert isinstance(resolver.type, LazyType)
    assert resolver.type is LazierType
    assert resolver.type.resolve_type() is LaziestType
