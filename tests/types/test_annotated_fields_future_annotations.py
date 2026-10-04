from __future__ import annotations

import sys
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

import pytest

import strawberry
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
    PrivateStrawberryFieldError,
    UnresolvedStrawberryFieldError,
)
from strawberry.extensions import FieldExtension
from strawberry.permission import BasePermission, PermissionExtension
from strawberry.types import get_object_definition
from strawberry.types.auto import StrawberryAuto
from strawberry.types.lazy_type import LazyType

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_c import TypeC
    from tests.schema.test_lazy.type_c import TypeC as NotDefinedYet
    from tests.schema.test_lazy.type_c import TypeC as UnresolvableType


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

T = TypeVar("T")
Described = Annotated[T, strawberry.field(description="Described")]
DESCRIBED = strawberry.field(description="Described")

# Python 3.14 evaluates the annotations of types defined later partially, so
# their `strawberry.field()` options can be read
READS_OPTIONS_OF_LATER_TYPES = sys.version_info >= (3, 14)


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
        overridden_result: Annotated[
            bool,
            strawberry.field(
                graphql_type=Success | Failure,
                description="The overridden result",
            ),
            strawberry.union("NamedOverriddenResult"),
        ]

    fields = {field.python_name: field for field in get_object_definition(Query).fields}

    assert fields["result"].description == "The result"
    assert fields["result"].type.graphql_name == "NamedResult"
    assert fields["overridden_result"].description == "The overridden result"
    assert fields["overridden_result"].type.graphql_name == "NamedOverriddenResult"

    schema = str(strawberry.Schema(query=Query))

    assert "union NamedResult = Success | Failure" in schema
    assert "union NamedOverriddenResult = Success | Failure" in schema


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


@pytest.mark.raises_strawberry_exception(
    InvalidStrawberryFieldAnnotationError,
    match=(
        r"`strawberry.field\(\)` for field `values` on type `Query` "
        r"must be placed at the top level of the field annotation"
    ),
)
def test_nested_annotated_field_raises_error():
    @strawberry.type
    class Query:
        values: list[Annotated[str, strawberry.field(description="Not the list field")]]


def test_nested_annotated_field_with_later_forward_reference_raises_error():
    def create_schema() -> None:
        global LaterWithNestedField

        @strawberry.type
        class Query:
            values: list[
                Annotated[
                    LaterWithNestedField,
                    strawberry.field(description="Not the list field"),
                ]
            ]

        @strawberry.type
        class LaterWithNestedField:
            value: str

        strawberry.Schema(query=Query)

    try:
        with pytest.raises(
            InvalidStrawberryFieldAnnotationError,
            match=(
                r"`strawberry.field\(\)` for field `values` on type `Query` "
                r"must be placed at the top level of the field annotation"
            ),
        ):
            create_schema()
    finally:
        globals().pop("LaterWithNestedField", None)


def test_nested_annotated_field_with_unresolvable_type_raises_error():
    with pytest.raises(InvalidStrawberryFieldAnnotationError):

        @strawberry.type
        class Query:
            values: list[
                Annotated[UnresolvableType, strawberry.field(description="Nested")]
            ]


def test_field_options_with_a_type_only_imported_for_type_checking():
    def create_type() -> type:
        @strawberry.type
        class Query:
            values: Annotated[
                list[NotDefinedYet],
                strawberry.field(description="The list field"),
            ]

        return Query

    if not READS_OPTIONS_OF_LATER_TYPES:
        with pytest.raises(
            UnresolvedStrawberryFieldError,
            match=(
                r"The `strawberry.field\(\)` options of field `values` on type "
                r"`Query` can't be read, because `NotDefinedYet` isn't defined yet"
            ),
        ):
            create_type()

        return

    field = get_object_definition(create_type(), strict=True).fields[0]

    assert field.description == "The list field"


def test_field_options_with_strawberry_lazy_are_read():
    @strawberry.type
    class Query:
        value: Annotated[
            TypeC,
            strawberry.lazy("tests.schema.test_lazy.type_c"),
            strawberry.field(description="The value"),
        ]

    field = get_object_definition(Query, strict=True).fields[0]

    assert field.description == "The value"
    assert isinstance(field.type, LazyType)
    assert field.type.resolve_type().__name__ == "TypeC"


skip_if_options_of_later_types_are_read = pytest.mark.skipif(
    READS_OPTIONS_OF_LATER_TYPES,
    reason="Python 3.14 reads the options of types defined later",
)


@skip_if_options_of_later_types_are_read
def test_permissions_on_a_type_not_defined_yet_raise_error():
    # `NotDefinedYet` is only imported for type checking, like a type defined later
    with pytest.raises(
        UnresolvedStrawberryFieldError,
        match=(
            r"The `strawberry.field\(\)` options of field `value` on type `Query` "
            r"can't be read, because `NotDefinedYet` isn't defined yet"
        ),
    ):

        @strawberry.type
        class Query:
            value: Annotated[
                NotDefinedYet, strawberry.field(permission_classes=[AllowAll])
            ]


@skip_if_options_of_later_types_are_read
def test_shared_field_on_a_type_not_defined_yet_raises_error():
    with pytest.raises(UnresolvedStrawberryFieldError):

        @strawberry.type
        class Query:
            value: Annotated[NotDefinedYet, DESCRIBED]


@skip_if_options_of_later_types_are_read
def test_annotated_alias_on_a_type_not_defined_yet_raises_error():
    with pytest.raises(UnresolvedStrawberryFieldError):

        @strawberry.type
        class Query:
            value: Described[NotDefinedYet]


@skip_if_options_of_later_types_are_read
def test_federation_field_on_a_type_not_defined_yet_raises_error():
    with pytest.raises(UnresolvedStrawberryFieldError):

        @strawberry.type
        class Query:
            value: Annotated[NotDefinedYet, strawberry.federation.field(shareable=True)]


def admin_only() -> Any:
    return strawberry.field(permission_classes=[AllowAll])


@skip_if_options_of_later_types_are_read
def test_field_from_a_helper_on_a_type_not_defined_yet_raises_error():
    with pytest.raises(UnresolvedStrawberryFieldError):

        @strawberry.type
        class Query:
            value: Annotated[NotDefinedYet, admin_only()]


@skip_if_options_of_later_types_are_read
def test_self_reference_with_field_options_raises_error():
    with pytest.raises(
        UnresolvedStrawberryFieldError,
        match=r"because `SelfReference` isn't defined yet",
    ):

        @strawberry.type
        class SelfReference:
            parent: Annotated[
                SelfReference | None, strawberry.field(description="The parent")
            ] = None


def test_field_options_as_the_default_of_a_type_not_defined_yet():
    global Tree

    try:

        @strawberry.type
        class Tree:
            parent: Tree | None = strawberry.field(
                description="The parent", default=None
            )

        field = get_object_definition(Tree, strict=True).fields[0]

        assert field.description == "The parent"
        assert "parent: Tree" in str(strawberry.Schema(query=Tree))
    finally:
        globals().pop("Tree", None)


def test_quoted_lazy_type_with_field_options():
    @strawberry.type
    class Query:
        value: Annotated[
            "TypeC",  # noqa: UP037
            strawberry.lazy("tests.schema.test_lazy.type_c"),
            strawberry.field(description="The value"),
        ]

    field = get_object_definition(Query, strict=True).fields[0]

    assert field.description == "The value"
    assert field.type.resolve_type().__name__ == "TypeC"


def test_fields_named_like_the_types_they_use_are_not_rejected():
    @strawberry.type
    class Event:
        @strawberry.field
        def date(self) -> date:
            return date(2026, 1, 1)

        previous: date | None = None

    schema = strawberry.Schema(query=Event)

    assert "previous: Date" in str(schema)
    assert schema.execute_sync("{ date previous }", root_value=Event()).data == {
        "date": "2026-01-01",
        "previous": None,
    }


def test_types_not_defined_yet_without_field_options_are_not_rejected():
    global LaterWithoutOptions

    try:

        @strawberry.type
        class Query:
            value: LaterWithoutOptions
            optional: LaterWithoutOptions | None = None
            values: list[LaterWithoutOptions] = strawberry.field(default_factory=list)

        @strawberry.type
        class LaterWithoutOptions:
            name: str

        schema = strawberry.Schema(query=Query)

        assert "value: LaterWithoutOptions!" in str(schema)
        assert "optional: LaterWithoutOptions" in str(schema)
        assert "values: [LaterWithoutOptions!]!" in str(schema)
    finally:
        globals().pop("LaterWithoutOptions", None)


def test_nested_lazy_metadata_is_preserved():
    @strawberry.type
    class Query:
        children: Annotated[
            list[Annotated[TypeC, strawberry.lazy("tests.schema.test_lazy.type_c")]],
            strawberry.field(description="The children"),
        ]

    field = get_object_definition(Query).fields[0]

    assert field.description == "The children"
    assert isinstance(field.type.of_type, LazyType)
    assert field.type.of_type.resolve_type().__name__ == "TypeC"


@pytest.mark.skipif(
    not READS_OPTIONS_OF_LATER_TYPES,
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
