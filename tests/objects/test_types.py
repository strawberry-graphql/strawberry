from dataclasses import dataclass

import pytest

import strawberry
from strawberry.exceptions import ObjectIsNotClassError


@pytest.mark.raises_strawberry_exception(
    ObjectIsNotClassError,
    match=(
        r"strawberry.type can only be used with class types. Provided "
        r"object .* is not a type."
    ),
)
def test_raises_error_when_using_type_with_a_not_class_object():
    @strawberry.type
    def not_a_class():
        pass


@pytest.mark.raises_strawberry_exception(
    ObjectIsNotClassError,
    match=(
        r"strawberry.input can only be used with class types. Provided "
        r"object .* is not a type."
    ),
)
def test_raises_error_when_using_input_with_a_not_class_object():
    @strawberry.input
    def not_a_class():
        pass


@pytest.mark.raises_strawberry_exception(
    ObjectIsNotClassError,
    match=(
        r"strawberry.interface can only be used with class types. Provided "
        r"object .* is not a type."
    ),
)
def test_raises_error_when_using_interface_with_a_not_class_object():
    @strawberry.interface
    def not_a_class():
        pass


def test_type_with_dataclass():
    @strawberry.type
    @dataclass(repr=False)
    class ClassWithNoRepr:
        number: int

    instance = ClassWithNoRepr(number=5)
    assert "ClassWithNoRepr object at" in repr(instance)


def test_type_with_dataclass_inheritance():
    @strawberry.type
    class A:
        number: int

    @strawberry.type
    @dataclass(repr=False)
    class B(A):
        string: str

    instance = B(number=5, string="foo")
    # note: `number` is included in the repr of B because `number` is part of
    # `A` which was created with `repr=True`.
    # `string` is correctly missing from the repr of `B` because `B` has been
    # created with `repr=False`.
    assert "B(number=5)" in repr(instance)

    instance2 = A(number=3)
    assert "A(number=3)" in repr(instance2)
