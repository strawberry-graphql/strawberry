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
