from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any

import pytest

import strawberry
from strawberry.exceptions import (
    MultipleStrawberryFieldsError,
    PrivateStrawberryFieldError,
)
from strawberry.extensions import FieldExtension
from strawberry.permission import BasePermission, PermissionExtension
from strawberry.types import get_object_definition
from strawberry.types.auto import StrawberryAuto
from strawberry.types.lazy_type import LazyType

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_c import TypeC


class AllowAll(BasePermission):
    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return True


class MarkerExtension(FieldExtension):
    pass


class Colour(Enum):
    RED = "red"


DIRECTIVE = object()
EXTENSION = MarkerExtension()

ConfiguredName = Annotated[
    str,
    strawberry.field(
        name="displayName",
        description="The displayed name",
        default="Anonymous",
    ),
]
Tags = Annotated[list[str], strawberry.field(default_factory=list)]


@strawberry.type
class Success:
    value: str


@strawberry.type
class Failure:
    message: str


def resolve_value() -> str:
    return "resolved"


def test_annotated_fields_on_all_type_definitions():
    @strawberry.type
    class ObjectType:
        name: ConfiguredName
        tags: Tags

    @strawberry.input
    class InputType:
        name: ConfiguredName
        tags: Tags

    @strawberry.interface
    class InterfaceType:
        name: ConfiguredName
        tags: Tags

    for type_ in (ObjectType, InputType, InterfaceType):
        fields = {
            field.python_name: field for field in get_object_definition(type_).fields
        }
        instance = type_()

        assert fields["name"].graphql_name == "displayName"
        assert fields["name"].description == "The displayed name"
        assert fields["name"].default == "Anonymous"
        assert fields["tags"].default_factory is list
        assert instance.name == "Anonymous"
        assert instance.tags == []
        assert instance.tags is not type_().tags


def test_annotated_field_supports_all_options():
    @strawberry.type
    class Query:
        value: Annotated[
            str,
            strawberry.field(
                name="renamed",
                is_subscription=True,
                description="A value",
                permission_classes=[AllowAll],
                deprecation_reason="Use another field",
                default="default",
                metadata={"key": "value"},
                directives=[DIRECTIVE],
                extensions=[EXTENSION],
            ),
        ]
        graphql_type_override: Annotated[
            bool,
            strawberry.field(graphql_type=int, default=True),
        ]
        resolved: Annotated[str, strawberry.field(resolver=resolve_value)]

    fields = {field.python_name: field for field in get_object_definition(Query).fields}
    field = fields["value"]
    instance = Query()

    assert field.graphql_name == "renamed"
    assert field.is_subscription is True
    assert field.description == "A value"
    assert field.permission_classes == [AllowAll]
    assert field.deprecation_reason == "Use another field"
    assert field.default == "default"
    assert field.metadata == {"key": "value"}
    assert field.directives == [DIRECTIVE]
    assert field.extensions.count(EXTENSION) == 1
    assert sum(isinstance(item, PermissionExtension) for item in field.extensions) == 1
    assert fields["graphql_type_override"].type is int
    assert fields["resolved"].base_resolver is not None
    assert instance.value == "default"
    assert instance.graphql_type_override is True


def test_annotated_field_preserves_union_metadata():
    @strawberry.type
    class Query:
        result: Annotated[
            Success | Failure,
            strawberry.union("NamedResult"),
            strawberry.field(description="The result"),
        ]

    field = get_object_definition(Query).fields[0]

    assert field.description == "The result"
    assert field.type.graphql_name == "NamedResult"
    assert "union NamedResult = Success | Failure" in str(
        strawberry.Schema(query=Query)
    )


def test_annotated_field_preserves_other_type_metadata():
    @strawberry.type
    class Query:
        colour: Annotated[
            Colour,
            strawberry.enum(name="AnnotatedColour", description="A colour"),
            strawberry.field(description="The selected colour"),
        ]
        child: Annotated[
            TypeC,
            strawberry.lazy("tests.schema.test_lazy.type_c"),
            strawberry.field(description="A lazy child"),
        ]
        inferred: Annotated[
            strawberry.auto,
            strawberry.field(description="An inferred field"),
        ]

    fields = {field.python_name: field for field in get_object_definition(Query).fields}

    assert fields["colour"].description == "The selected colour"
    assert fields["colour"].type.name == "AnnotatedColour"
    assert fields["colour"].type.description == "A colour"
    assert fields["child"].description == "A lazy child"
    assert isinstance(fields["child"].type, LazyType)
    assert fields["child"].type.resolve_type().__name__ == "TypeC"
    assert fields["inferred"].description == "An inferred field"
    assert isinstance(fields["inferred"].type_annotation, StrawberryAuto)


def test_annotated_field_preserves_private_metadata():
    with pytest.raises(PrivateStrawberryFieldError):

        @strawberry.type
        class Query:
            secret: Annotated[
                strawberry.Private[str],
                strawberry.field(description="A secret"),
            ]


def test_multiple_annotated_fields_raise_error():
    with pytest.raises(MultipleStrawberryFieldsError):

        @strawberry.type
        class Query:
            value: Annotated[
                str,
                strawberry.field(description="First"),
                strawberry.field(description="Second"),
            ]


@pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="partial forward-reference evaluation requires Python 3.14",
)
def test_annotated_field_with_unresolved_forward_reference():
    global Later

    try:

        @strawberry.type
        class Query:
            later: Annotated[Later, strawberry.field(description="Defined later")]

        @strawberry.type
        class Later:
            value: str

        field = get_object_definition(Query).fields[0]

        assert field.description == "Defined later"
        assert field.type is Later
        assert "later: Later!" in str(strawberry.Schema(query=Query))
    finally:
        del Later
