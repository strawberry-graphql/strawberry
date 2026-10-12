"""The helpers that read `strawberry.field()` and other options from `Annotated`.

They're shared by `@strawberry.type` and integrations, which can read their own
options, like Pydantic's `Field()`.
"""

from typing import Annotated, Any, TypeVar

import pytest

import strawberry
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.types.field import StrawberryField, get_annotated_field
from strawberry.types.unresolved_annotations import (
    UnresolvedOptions,
    find_unresolved_options,
)

T = TypeVar("T")


class Option:
    """Metadata an integration reads as an option, like Pydantic's `Field()`."""


class Model:
    pass


def is_option(value: object) -> bool:
    return isinstance(value, (Option, StrawberryField))


NAMESPACE: dict[str, Any] = {
    "Annotated": Annotated,
    "Option": Option,
    "strawberry": strawberry,
    # aliases defined before the model, using `Account`, which is defined later
    "Hidden": Annotated[list["Account"], Option()],  # noqa: F821
    "AdminOnly": Annotated[T, Option()],
}


def find(annotation: str, **kwargs: Any) -> UnresolvedOptions | None:
    return find_unresolved_options(
        annotation, NAMESPACE, cls=Model, field_name="account", **kwargs
    )


def test_get_annotated_field():
    field = strawberry.field(name="age")

    assert get_annotated_field(
        Annotated[int, field, "doc"], cls=Model, field_name="age"
    ) == (Annotated[int, "doc"], field)
    assert get_annotated_field(Annotated[int, field], cls=Model, field_name="age") == (
        int,
        field,
    )


def test_get_annotated_field_without_a_field():
    assert get_annotated_field(Annotated[int, "doc"], cls=Model, field_name="age") == (
        Annotated[int, "doc"],
        None,
    )
    assert get_annotated_field(int, cls=Model, field_name="age") == (int, None)


def test_get_annotated_field_with_several_fields_raises_an_error():
    with pytest.raises(MultipleStrawberryFieldsError):
        get_annotated_field(
            Annotated[int, strawberry.field(), strawberry.field()],
            cls=Model,
            field_name="age",
        )


def test_get_annotated_field_with_a_nested_field_raises_an_error():
    with pytest.raises(InvalidStrawberryFieldAnnotationError):
        get_annotated_field(
            list[Annotated[int, strawberry.field()]], cls=Model, field_name="age"
        )


def test_strawberry_fields_are_the_options_by_default():
    assert find('Annotated[Account, strawberry.field(name="owner")]') == (
        UnresolvedOptions(undefined_names=["Account"], in_options=False)
    )
    assert find("Annotated[Account, Option()]") is None


def test_options_are_what_is_option_accepts():
    assert find("Annotated[Account, Option()]", is_option=is_option) == (
        UnresolvedOptions(undefined_names=["Account"], in_options=False)
    )


def test_annotations_without_options_can_be_resolved_later():
    assert find("list[Account]", is_option=is_option) is None
    assert find('Annotated[Account, "doc"]', is_option=is_option) is None


def test_metadata_that_cant_be_evaluated_yet_could_be_an_option():
    # e.g. a permission class defined after the model, while the type is defined
    assert find("Annotated[str, Option(Later)]", is_option=is_option) == (
        UnresolvedOptions(undefined_names=["Later"], in_options=True)
    )


def test_aliases_with_options():
    assert find("Hidden", is_option=is_option) == (
        UnresolvedOptions(undefined_names=[], in_options=False)
    )
    assert find("AdminOnly[Account]", is_option=is_option) == (
        UnresolvedOptions(undefined_names=["Account"], in_options=False)
    )
    assert find("AdminOnly[Account]") is None


def test_nested_options_are_not_read():
    # like `list[Annotated[int, Field(gt=0)]]`, they don't configure the field
    assert find("list[Annotated[Account, Option()]]", is_option=is_option) is None


def test_nested_strawberry_fields_raise_an_error():
    with pytest.raises(InvalidStrawberryFieldAnnotationError):
        find("list[Annotated[Account, strawberry.field()]]", is_option=is_option)
