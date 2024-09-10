from typing import List

import pytest

import strawberry
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    InvalidDefaultFactoryError,
)
from strawberry.types.field import StrawberryField


def test_field_with_default():
    @strawberry.type
    class Query:
        the_field: int = strawberry.field(default=3)

    instance = Query()
    assert instance.the_field == 3


def test_field_with_resolver_and_default():
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        @strawberry.type
        class Query:
            @strawberry.field(default="potato")
            def fruit(self) -> str:
                return "tomato"


def test_field_with_default_factory():
    @strawberry.type
    class Query:
        the_int: int = strawberry.field(default_factory=lambda: 3)

    instance = Query()
    [int_field] = Query.__strawberry_definition__.fields

    assert instance.the_int == 3
    assert int_field.default_value == 3


def test_field_default_extensions_value_set():
    field = StrawberryField(python_name="test", default="test")
    assert field.extensions == []


def test_field_default_factory_executed_each_time():
    @strawberry.type
    class Query:
        the_list: List[str] = strawberry.field(default_factory=list)

    assert Query().the_list == Query().the_list
    assert Query().the_list is not Query().the_list


def test_field_with_separate_resolver_default():
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        def gun_resolver() -> str:
            return "revolver"

        @strawberry.type
        class Query:
            weapon: str = strawberry.field(default="sword", resolver=gun_resolver)


def test_field_with_resolver_and_default_factory():
    with pytest.raises(FieldWithResolverAndDefaultFactoryError):

        @strawberry.type
        class Query:
            @strawberry.field(default_factory=lambda: "steel")
            def metal(self) -> str:
                return "iron"


def test_invalid_default_factory():
    with pytest.raises(InvalidDefaultFactoryError):
        strawberry.field(default_factory=round)
