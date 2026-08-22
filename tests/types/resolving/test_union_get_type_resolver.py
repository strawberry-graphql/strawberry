"""Tests for StrawberryUnion.get_type_resolver method and the resolver function it returns."""

from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar
from unittest.mock import MagicMock

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion
from strawberry.schema.types.concrete_type import TypeMap
from strawberry.types.union import StrawberryUnion


def test_get_type_resolver_returns_function():
    """Test that get_type_resolver returns a callable function."""

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    union = StrawberryUnion(
        type_annotations=(
            StrawberryAnnotation(A),
            StrawberryAnnotation(B),
        )
    )

    type_map: TypeMap = {}
    resolver = union.get_type_resolver(type_map)

    assert callable(resolver)


def test_type_resolver_with_object_definition():
    """Test that the resolver correctly resolves types when root has object definition."""

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    # Create a schema to get proper GraphQL types
    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> A | B:
            return A(a=1)

    schema = strawberry.Schema(query=Query)

    # Find the union in the schema's type map
    union_name = None
    union_def = None
    for name, concrete_type in schema.schema_converter.type_map.items():
        if isinstance(concrete_type.definition, StrawberryUnion):
            union_name = name
            union_def = concrete_type.definition
            break

    assert union_name is not None, "Union should be in type map"
    assert union_def is not None, "Union definition should be found"
    graphql_union = schema.schema_converter.type_map[union_name].implementation

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "test"

    # Test with A instance
    a_instance = A(a=1)
    result = resolver(a_instance, info, graphql_union)
    assert result == "A"

    # Test with B instance
    b_instance = B(b=2)
    result = resolver(b_instance, info, graphql_union)
    assert result == "B"


def test_type_resolver_with_is_type_of():
    """Test that the resolver uses is_type_of when root doesn't have object definition."""

    @dataclass
    class ADataclass:
        a: int

    @dataclass
    class BDataclass:
        b: int

    @strawberry.type
    class A:
        a: int

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, ADataclass)

    @strawberry.type
    class B:
        b: int

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, BDataclass)

    # Create a schema to get proper GraphQL types
    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> A | B:
            return ADataclass(a=1)  # type: ignore

    schema = strawberry.Schema(query=Query)

    # Find the union in the schema's type map
    union_name = None
    union_def = None
    for name, concrete_type in schema.schema_converter.type_map.items():
        if isinstance(concrete_type.definition, StrawberryUnion):
            union_name = name
            union_def = concrete_type.definition
            break

    assert union_name is not None, "Union should be in type map"
    assert union_def is not None, "Union definition should be found"
    graphql_union = schema.schema_converter.type_map[union_name].implementation

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "test"

    # Test with ADataclass instance (should resolve to A)
    a_dataclass = ADataclass(a=1)
    result = resolver(a_dataclass, info, graphql_union)
    assert result == "A"

    # Test with BDataclass instance (should resolve to B)
    b_dataclass = BDataclass(b=2)
    result = resolver(b_dataclass, info, graphql_union)
    assert result == "B"


def test_type_resolver_raises_wrong_return_type_when_no_is_type_of_matches():
    """Test that the resolver raises WrongReturnTypeForUnion when is_type_of doesn't match."""

    @dataclass
    class UnknownDataclass:
        x: int

    @strawberry.type
    class A:
        a: int

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return False  # This won't match

    @strawberry.type
    class B:
        b: int

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return False  # This won't match either

    # Create a schema to get proper GraphQL types
    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> A | B:
            return UnknownDataclass(x=1)  # type: ignore

    schema = strawberry.Schema(query=Query)

    # Find the union in the schema's type map
    union_name = None
    union_def = None
    for name, concrete_type in schema.schema_converter.type_map.items():
        if isinstance(concrete_type.definition, StrawberryUnion):
            union_name = name
            union_def = concrete_type.definition
            break

    assert union_name is not None, "Union should be in type map"
    assert union_def is not None, "Union definition should be found"
    graphql_union = schema.schema_converter.type_map[union_name].implementation

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "test"

    # Test with UnknownDataclass instance (should raise error)
    unknown_instance = UnknownDataclass(x=1)
    with pytest.raises(WrongReturnTypeForUnion) as exc_info:
        resolver(unknown_instance, info, graphql_union)

    assert "test" in str(exc_info.value)
    assert "UnknownDataclass" in str(exc_info.value)


def test_type_resolver_raises_unallowed_return_type_when_not_in_union():
    """Test that the resolver raises UnallowedReturnTypeForUnion when type is not in union."""

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Outside:
        c: int

    # Create a schema that includes Outside but not in the union
    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> A | B:
            return Outside(c=1)  # type: ignore

    schema = strawberry.Schema(query=Query, types=[Outside])

    # Find the union in the schema's type map
    union_name = None
    union_def = None
    for name, concrete_type in schema.schema_converter.type_map.items():
        if isinstance(concrete_type.definition, StrawberryUnion):
            union_name = name
            union_def = concrete_type.definition
            break

    assert union_name is not None, "Union should be in type map"
    assert union_def is not None, "Union definition should be found"
    graphql_union = schema.schema_converter.type_map[union_name].implementation

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "test"

    # Test with Outside instance (should raise error)
    outside_instance = Outside(c=1)
    with pytest.raises(UnallowedReturnTypeForUnion) as exc_info:
        resolver(outside_instance, info, graphql_union)

    assert "test" in str(exc_info.value)
    assert "Outside" in str(exc_info.value)
    assert "A" in str(exc_info.value) or "B" in str(exc_info.value)


def test_type_resolver_prioritizes_union_types():
    """Test that the resolver prioritizes union types over other types in type_map.

    This tests the bug fix from PR #1463 where union types should be checked first
    before falling back to all types in the type_map.
    """
    T = TypeVar("T")

    @strawberry.type
    class Container(Generic[T]):
        items: list[T]

    @strawberry.type
    class A:
        a: str

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        @strawberry.field
        def container_a(self) -> Container[A] | A:
            return Container(items=[A(a="hello")])

        @strawberry.field
        def container_b(self) -> Container[B] | B:
            return Container(items=[B(b=3)])

    schema = strawberry.Schema(query=Query)

    # Find the union for Container[A] | A in the schema's type map
    # We'll look for a union that has "AContainer" in its name (generated by schema)
    union_name = None
    union_def = None
    for name, concrete_type in schema.schema_converter.type_map.items():
        if isinstance(concrete_type.definition, StrawberryUnion):
            # Check if this union name contains "AContainer" (indicating Container[A] | A)
            # and check if A is in the union types
            union_types = concrete_type.definition.types
            has_a = A in union_types
            if "AContainer" in name and has_a:
                union_name = name
                union_def = concrete_type.definition
                break

    assert union_name is not None, "Union Container[A] | A should be in type map"
    assert union_def is not None, "Union definition should be found"
    graphql_union = schema.schema_converter.type_map[union_name].implementation

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "containerA"

    # Test with Container[A] instance - should resolve to Container[A], not Container[B]
    container_a_instance = Container(items=[A(a="hello")])
    result = resolver(container_a_instance, info, graphql_union)

    # Should resolve to the Container[A] type name
    assert result == "AContainer"

    # Test with A instance
    a_instance = A(a="hello")
    result = resolver(a_instance, info, graphql_union)
    assert result == "A"


def test_type_resolver_with_single_type_union():
    """Test that the resolver works correctly with a single-type union."""

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> Annotated[A, strawberry.union(name="SingleUnion")]:
            return A(a=1)

    schema = strawberry.Schema(query=Query)
    graphql_union = schema.schema_converter.type_map["SingleUnion"].implementation
    union_def = schema.schema_converter.type_map["SingleUnion"].definition
    assert isinstance(union_def, StrawberryUnion), "Should be a StrawberryUnion"

    # Get the resolver from the union
    resolver = union_def.get_type_resolver(schema.schema_converter.type_map)

    # Create mock info
    info = MagicMock()
    info.field_name = "test"

    # Test with A instance
    a_instance = A(a=1)
    result = resolver(a_instance, info, graphql_union)
    assert result == "A"
