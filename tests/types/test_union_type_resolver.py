"""Unit tests for StrawberryUnion.get_type_resolver and the resolver it returns.

Directly tests the _resolve_union_type inner function, covering:
- Correct type name returned for a strawberry-typed object.
- Fallback to is_type_of when the object has no strawberry definition.
- WrongReturnTypeForUnion raised when neither strategy resolves the type.
- UnallowedReturnTypeForUnion raised when the resolved type is not in the union.
"""

from dataclasses import dataclass
from typing import Annotated
from unittest.mock import MagicMock

import pytest

import strawberry
from strawberry.exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion


def _mock_info(field_name: str = "animal"):
    info = MagicMock()
    info.field_name = field_name
    return info


def _get_union_resolver(schema, union_name: str):
    """Return the StrawberryUnion type resolver for the named union."""
    type_map = schema.schema_converter.type_map
    union_def = type_map[union_name].definition
    return union_def.get_type_resolver(type_map)


def _gql_union(schema, union_name: str):
    """Return the graphql-core GraphQLUnionType for the named union."""
    return schema._schema.type_map[union_name]


def test_get_type_resolver_returns_callable():
    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    Animal = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return Cat(name="Whiskers")

    schema = strawberry.Schema(query=Query)
    resolver = _get_union_resolver(schema, "Animal")
    assert callable(resolver)


def test_resolver_returns_correct_type_name_for_strawberry_object():
    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    Animal = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return Cat(name="Whiskers")

    schema = strawberry.Schema(query=Query)
    resolver = _get_union_resolver(schema, "Animal")
    gql_union = _gql_union(schema, "Animal")

    assert resolver(Cat(name="Whiskers"), _mock_info(), gql_union) == "Cat"
    assert resolver(Dog(name="Rex"), _mock_info(), gql_union) == "Dog"


def test_resolver_uses_is_type_of_for_non_strawberry_objects():
    """When root has no strawberry definition, resolver falls back to is_type_of."""

    @dataclass
    class CatData:
        name: str

    @dataclass
    class DogData:
        name: str

    @strawberry.type
    class Cat:
        name: str

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, CatData)

    @strawberry.type
    class Dog:
        name: str

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, DogData)

    Animal = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return CatData(name="Whiskers")  # type: ignore[return-value]

    schema = strawberry.Schema(query=Query)
    resolver = _get_union_resolver(schema, "Animal")
    gql_union = _gql_union(schema, "Animal")

    assert resolver(CatData(name="Whiskers"), _mock_info(), gql_union) == "Cat"
    assert resolver(DogData(name="Rex"), _mock_info(), gql_union) == "Dog"


def test_resolver_raises_wrong_return_type_when_no_definition_and_no_is_type_of():
    """WrongReturnTypeForUnion raised when root has no definition and no is_type_of."""

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    Animal = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return Cat(name="Whiskers")

    schema = strawberry.Schema(query=Query)
    resolver = _get_union_resolver(schema, "Animal")
    gql_union = _gql_union(schema, "Animal")

    # A plain dict has no strawberry definition and union types have no is_type_of
    with pytest.raises(WrongReturnTypeForUnion):
        resolver({"name": "Unknown"}, _mock_info(), gql_union)


def test_resolver_raises_unallowed_return_type_for_unrelated_strawberry_object():
    """UnallowedReturnTypeForUnion raised when object type is not part of the union."""

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    @strawberry.type
    class Fish:
        name: str

    Animal = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return Cat(name="Whiskers")

    # Fish is registered in the schema but NOT part of the Animal union
    schema = strawberry.Schema(query=Query, types=[Fish])
    resolver = _get_union_resolver(schema, "Animal")
    gql_union = _gql_union(schema, "Animal")

    with pytest.raises(UnallowedReturnTypeForUnion):
        resolver(Fish(name="Nemo"), _mock_info(), gql_union)
