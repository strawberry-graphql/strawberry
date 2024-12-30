import textwrap
from typing import Any

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
)
from strawberry.extensions.field_extension import FieldExtension
from strawberry.types.field import StrawberryField


def test_field_with_resolver_default():
    with pytest.raises(FieldWithResolverAndDefaultValueError):

        @strawberry.type
        class Query:
            @strawberry.field(default="potato")
            def fruit(self) -> str:
                return "tomato"


def test_field_with_separate_resolver_default():
    def fruit_resolver() -> str:  # pragma: no cover
        return "strawberry"

    with pytest.raises(FieldWithResolverAndDefaultValueError):

        @strawberry.type
        class Query:
            weapon: str = strawberry.field(default="banana", resolver=fruit_resolver)


def test_field_with_resolver_default_factory():
    with pytest.raises(FieldWithResolverAndDefaultFactoryError):

        @strawberry.type
        class Query:
            @strawberry.field(default_factory=lambda: "steel")
            def metal(self) -> str:
                return "iron"


def test_extension_changing_field_return_value():
    """Ensure that field extensions can change the field's return type."""

    class ChangeReturnTypeExtension(FieldExtension):
        def apply(self, field: StrawberryField) -> None:
            field.type_annotation = StrawberryAnnotation.from_annotation(int)

        def resolve(self, next_, source, info, **kwargs: Any):
            return next_(source, info, **kwargs)

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[ChangeReturnTypeExtension()])
        def test_changing_return_type(self) -> bool: ...

    schema = strawberry.Schema(query=Query)
    expected = """\
      type Query {
        testChangingReturnType: Int!
      }
    """
    assert str(schema) == textwrap.dedent(expected).strip()
