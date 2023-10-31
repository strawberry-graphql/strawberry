from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.annotation import StrawberryTypeVar
from strawberry.type import get_object_definition

T = TypeVar("T")


@pytest.mark.xfail(reason="This should be fixed")
def test_basic_generic():
    directive = object()

    @strawberry.interface
    class Edge(Generic[T]):
        node_field: T = strawberry.field(directives=[directive])

    definition = get_object_definition(Edge, strict=True)
    assert definition.is_generic
    assert definition.type_params == [T]

    [field] = definition.fields
    assert field.python_name == "node_field"
    assert isinstance(field.type, StrawberryTypeVar)
    assert field.type.type_var is T

    @strawberry.type
    class User(Edge[str]):
        pass

    definition = get_object_definition(User, strict=True)

    assert not definition.is_generic
    assert definition.type_params == []
    assert definition.interfaces == [Edge[str]]

    [field_copy] = definition.fields
    assert field_copy.python_name == "node_field"
    assert field_copy.type is str
    assert field_copy.directives == [directive]
