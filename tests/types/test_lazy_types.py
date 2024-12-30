# type: ignore
import enum
import sys
import textwrap
from typing import Annotated, Generic, TypeVar, Union
from typing_extensions import TypeAlias

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import get_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.lazy_type import LazyType
from strawberry.types.union import StrawberryUnion, union

T = TypeVar("T")


# This type is in the same file but should adequately test the logic.
@strawberry.type
class LaziestType:
    something: bool


@strawberry.type
class LazyGenericType(Generic[T]):
    something: T


LazyTypeAlias: TypeAlias = LazyGenericType[int]


@strawberry.enum
class LazyEnum(enum.Enum):
    BREAD = "BREAD"


def test_lazy_type():
    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved is LazierType
    assert resolved.resolve_type() is LaziestType


def test_lazy_type_alias():
    LazierType = LazyType("LazyTypeAlias", "tests.types.test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    resolved_type = resolved.resolve_type()
    assert resolved_type.__origin__ is LazyGenericType
    assert resolved_type.__args__ == (int,)


def test_lazy_type_function():
    LethargicType = Annotated[
        "LaziestType", strawberry.lazy("tests.types.test_lazy_types")
    ]

    annotation = StrawberryAnnotation(LethargicType)
    resolved = annotation.resolve()

    assert isinstance(resolved, LazyType)
    assert resolved.resolve_type() is LaziestType


def test_lazy_type_enum():
    LazierType = LazyType("LazyEnum", "tests.types.test_lazy_types")

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved is LazierType
    assert resolved.resolve_type() is LazyEnum


def test_lazy_type_argument():
    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")

    @strawberry.mutation
    def slack_off(emotion: LazierType) -> bool:
        _ = emotion
        return True

    argument = slack_off.arguments[0]
    assert isinstance(argument.type, LazyType)
    assert argument.type is LazierType
    assert argument.type.resolve_type() is LaziestType


def test_lazy_type_field():
    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")

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

    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")
    ResolvedType = GenericType[LazierType]

    annotation = StrawberryAnnotation(ResolvedType)
    resolved = annotation.resolve()

    definition = get_object_definition(resolved)
    assert definition
    items_field: StrawberryField = definition.fields[0]
    assert items_field.type is LazierType
    assert items_field.type.resolve_type() is LaziestType


def test_lazy_type_object():
    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")

    @strawberry.type
    class WaterParkFeature:
        river: LazierType

    field: StrawberryField = WaterParkFeature.__strawberry_definition__.fields[0]

    assert isinstance(field.type, LazyType)
    assert field.type is LazierType
    assert field.type.resolve_type() is LaziestType


def test_lazy_type_resolver():
    LazierType = LazyType("LaziestType", "tests.types.test_lazy_types")

    def slaking_pokemon() -> LazierType:
        raise NotImplementedError

    resolver = StrawberryResolver(slaking_pokemon)
    assert isinstance(resolver.type, LazyType)
    assert resolver.type is LazierType
    assert resolver.type.resolve_type() is LaziestType


def test_lazy_type_in_union():
    ActiveType = LazyType("LaziestType", "tests.types.test_lazy_types")
    ActiveEnum = LazyType("LazyEnum", "tests.types.test_lazy_types")

    something = Annotated[Union[ActiveType, ActiveEnum], union(name="CoolUnion")]
    annotation = StrawberryAnnotation(something)

    resolved = annotation.resolve()
    assert isinstance(resolved, StrawberryUnion)

    [type1, type2] = resolved.types
    assert type1 is ActiveType
    assert type2 is ActiveEnum
    assert type1.resolve_type() is LaziestType
    assert type2.resolve_type() is LazyEnum


def test_lazy_function_in_union():
    ActiveType = Annotated[
        "LaziestType", strawberry.lazy("tests.types.test_lazy_types")
    ]
    ActiveEnum = Annotated["LazyEnum", strawberry.lazy("tests.types.test_lazy_types")]

    something = Annotated[Union[ActiveType, ActiveEnum], union(name="CoolUnion")]
    annotation = StrawberryAnnotation(something)

    resolved = annotation.resolve()
    assert isinstance(resolved, StrawberryUnion)

    [type1, type2] = resolved.types
    assert type1.resolve_type() is LaziestType
    assert type2.resolve_type() is LazyEnum


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="| operator without future annotations is only available on python 3.10+",
)
def test_optional_lazy_type_using_or_operator():
    from tests.schema.test_lazy.type_a import TypeA

    @strawberry.type
    class SomeType:
        foo: Annotated[TypeA, strawberry.lazy("tests.schema.test_lazy.type_a")] | None

    @strawberry.type
    class AnotherType:
        foo: TypeA | None = None

    @strawberry.type
    class Query:
        some_type: SomeType
        another_type: AnotherType

    schema = strawberry.Schema(query=Query)
    expected = """\
    type AnotherType {
      foo: TypeA
    }

    type Query {
      someType: SomeType!
      anotherType: AnotherType!
    }

    type SomeType {
      foo: TypeA
    }

    type TypeA {
      listOfB: [TypeB!]
      typeB: TypeB!
    }

    type TypeB {
      typeA: TypeA!
      typeAList: [TypeA!]!
      typeCList: [TypeC!]!
    }

    type TypeC {
      name: String!
    }
    """
    assert str(schema).strip() == textwrap.dedent(expected).strip()
