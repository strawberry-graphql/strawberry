import pytest

import strawberry
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    InvalidDefaultFactoryError,
)


def test_field_with_resolver_default():
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        @strawberry.type
        class Query:
            @strawberry.field(default="potato")
            def fruit(self) -> str:
                return "tomato"


def test_field_with_separate_resolver_default():
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        def gun_resolver() -> str:
            return "revolver"

        @strawberry.type
        class Query:
            weapon: str = strawberry.field(default="sword", resolver=gun_resolver)


def test_field_with_resolver_default_factory():
    with pytest.raises(FieldWithResolverAndDefaultFactoryError):

        @strawberry.type
        class Query:
            @strawberry.field(default_factory=lambda: "steel")
            def metal(self) -> str:
                return "iron"


def test_invalid_default_factory():
    with pytest.raises(InvalidDefaultFactoryError):
        strawberry.field(default_factory=round)
