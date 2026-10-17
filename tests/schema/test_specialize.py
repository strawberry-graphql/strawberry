import sys
import textwrap
import types
from typing import Annotated, Generic, TypeVar

import pytest

import strawberry
import strawberry.federation
from strawberry.exceptions import UndecoratedSubclassError
from strawberry.types.base import (
    StrawberryObjectDefinition,
    check_is_not_undecorated_subclass,
    get_object_definition,
    has_object_definition,
)

T = TypeVar("T")


def _box_types(argument: type = int) -> tuple[type, type, list[type]]:
    """A generic type, and a subclass specializing it with `argument`, like the
    classes pydantic creates for its parametrizations."""

    @strawberry.type
    class Box(Generic[T]):
        value: T

    class SpecializedBox(Box[argument]):  # type: ignore[valid-type]
        pass

    specialized: list[type] = []

    def specialize(cls: type) -> StrawberryObjectDefinition | None:
        if cls is not SpecializedBox:
            return None

        specialized.append(cls)

        definition = get_object_definition(
            box_definition.copy_with({"T": argument}), strict=True
        )
        definition.origin = cls

        return definition

    box_definition = get_object_definition(Box, strict=True)
    box_definition.specialize = specialize

    return Box, SpecializedBox, specialized


def test_subclasses_specializing_a_generic_type_get_their_own_definition():
    _, IntBox, specialized = _box_types()

    @strawberry.type
    class Query:
        box: IntBox  # type: ignore[valid-type]

        @strawberry.field
        def boxes(self) -> list[IntBox]:  # type: ignore[valid-type]
            return [IntBox(value=1)]

    schema = strawberry.Schema(query=Query)

    assert str(schema) == textwrap.dedent(
        """\
        type IntBox {
          value: Int!
        }

        type Query {
          box: IntBox!
          boxes: [IntBox!]!
        }"""
    )

    result = schema.execute_sync("{ boxes { value } }")

    assert not result.errors
    assert result.data == {"boxes": [{"value": 1}]}

    # the definition is kept on the class, so it's only built once
    assert specialized == [IntBox]
    assert vars(IntBox)["__strawberry_definition__"].origin is IntBox


def test_subclasses_specializing_a_generic_type_can_be_passed_to_the_schema():
    _, IntBox, _ = _box_types()

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.Schema(query=Query, types=[IntBox])

    assert "type IntBox {\n  value: Int!\n}" in str(schema)


def test_subclasses_that_dont_specialize_the_generic_type_raise_an_error():
    Box, _, _ = _box_types()

    class OtherBox(Box[str]):  # type: ignore[valid-type]
        pass

    @strawberry.type
    class Query:
        box: OtherBox  # type: ignore[valid-type]

    with pytest.raises(UndecoratedSubclassError) as exc_info:
        strawberry.Schema(query=Query)

    assert exc_info.value.cls is OtherBox


def test_reading_the_definition_specializes_subclasses():
    _, IntBox, specialized = _box_types()

    definition = IntBox.__strawberry_definition__

    assert specialized == [IntBox]
    assert vars(IntBox)["__strawberry_definition__"] is definition
    assert get_object_definition(IntBox) is definition
    assert specialized == [IntBox]


def test_reading_the_definition_from_an_instance_specializes_its_class():
    _, IntBox, specialized = _box_types()

    definition = IntBox(value=1).__strawberry_definition__

    assert specialized == [IntBox]
    assert vars(IntBox)["__strawberry_definition__"] is definition


def test_checking_for_undecorated_subclasses_specializes_them():
    _, IntBox, specialized = _box_types()

    # nothing has read the definition of `IntBox` yet
    check_is_not_undecorated_subclass(IntBox)

    assert specialized == [IntBox]


def test_attribute_errors_raised_while_specializing_are_not_hidden():
    Box, IntBox, _ = _box_types()

    def specialize(cls: type) -> StrawberryObjectDefinition | None:
        raise AttributeError("no attribute `value`")

    get_object_definition(Box, strict=True).specialize = specialize

    # `hasattr()` would otherwise make `IntBox` look like it has no definition
    with pytest.raises(
        RuntimeError,
        match="Couldn't build the definition of `SpecializedBox`: no attribute `value`",
    ):
        has_object_definition(IntBox)


def test_subclasses_resolved_from_lazy_references_are_specialized(
    monkeypatch: pytest.MonkeyPatch,
):
    _, IntBox, _ = _box_types()

    @strawberry.type
    class Other:
        name: str

    module = types.ModuleType("specialize_lazy_types")
    module.IntBox = IntBox  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, module.__name__, module)

    @strawberry.type
    class Query:
        # union names are made from the names of their types
        box: Annotated["IntBox", strawberry.lazy("specialize_lazy_types")] | Other

    schema = strawberry.Schema(query=Query)

    assert "union IntBoxOther = IntBox | Other" in str(schema)


def test_entities_reached_through_specialized_subclasses_are_found():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

    _, ProductBox, _ = _box_types(Product)

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.federation.Schema(query=Query, types=[ProductBox])

    assert schema.get_type_by_name("_Entity") is not None
