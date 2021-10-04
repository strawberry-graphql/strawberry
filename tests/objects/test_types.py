import pytest

import strawberry
from strawberry.exceptions import ObjectIsNotClassError


def test_raises_error_when_using_type_with_a_not_class_object():
    expected_error = (
        r"strawberry.type can only be used with class types. Provided "
        r"object .* is not a type."
    )

    with pytest.raises(ObjectIsNotClassError, match=expected_error):

        @strawberry.type
        def not_a_class():
            pass


def test_raises_error_when_using_input_with_a_not_class_object():
    expected_error = (
        r"strawberry.input can only be used with class types. Provided "
        r"object .* is not a type."
    )

    with pytest.raises(ObjectIsNotClassError, match=expected_error):

        @strawberry.input
        def not_a_class():
            pass


def test_raises_error_when_using_interface_with_a_not_class_object():
    expected_error = (
        r"strawberry.interface can only be used with class types. Provided "
        r"object .* is not a type."
    )

    with pytest.raises(ObjectIsNotClassError, match=expected_error):

        @strawberry.interface
        def not_a_class():
            pass
