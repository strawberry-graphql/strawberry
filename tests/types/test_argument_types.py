import warnings
from enum import Enum
from typing import Any, List, Optional, TypeVar

import pytest

from typing_extensions import Annotated

import strawberry
from strawberry.types.info import Info


def test_enum():
    @strawberry.enum
    class Locale(Enum):
        UNITED_STATES = "en_US"
        UK = "en_UK"
        AUSTRALIA = "en_AU"

    @strawberry.mutation
    def set_locale(locale: Locale) -> bool:
        _ = locale
        return True

    argument = set_locale.arguments[0]
    # TODO: Remove reference to ._enum_definition with StrawberryEnum
    assert argument.type is Locale._enum_definition


def test_forward_reference():
    global SearchInput

    @strawberry.field
    def search(search_input: "SearchInput") -> bool:
        _ = search_input
        return True

    @strawberry.input
    class SearchInput:
        query: str

    argument = search.arguments[0]
    assert argument.type is SearchInput

    del SearchInput


def test_list():
    @strawberry.field
    def get_longest_word(words: List[str]) -> str:
        _ = words
        return "I cheated"

    argument = get_longest_word.arguments[0]
    assert argument.type == List[str]


def test_literal():
    @strawberry.field
    def get_name(id_: int) -> str:
        _ = id_
        return "Lord Buckethead"

    argument = get_name.arguments[0]
    assert argument.type == int


def test_object():
    @strawberry.type
    class PersonInput:
        proper_noun: bool

    @strawberry.field
    def get_id(person_input: PersonInput) -> int:
        _ = person_input
        return 0

    argument = get_id.arguments[0]
    assert argument.type is PersonInput


def test_optional():
    @strawberry.field
    def set_age(age: Optional[int]) -> bool:
        _ = age
        return True

    argument = set_age.arguments[0]
    assert argument.type == Optional[int]


def test_type_var():
    T = TypeVar("T")

    @strawberry.field
    def set_value(value: T) -> bool:
        _ = value
        return True

    argument = set_value.arguments[0]
    assert argument.type == T


ContextType = TypeVar("ContextType")
RootValueType = TypeVar("RootValueType")


class CustomInfo(Info[ContextType, RootValueType]):
    """Subclassed Info type used to test dependency injection."""


@pytest.mark.parametrize(
    "annotation",
    [CustomInfo, CustomInfo[Any, Any], Info, Info[Any, Any]],
)
def test_custom_info(annotation):
    """Test to ensure that subclassed Info does not raise warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings("error")

        def get_info(info) -> bool:
            _ = info
            return True

        get_info.__annotations__["info"] = annotation
        get_info_field = strawberry.field(get_info)

        assert not get_info_field.arguments  # Should have no arguments matched

        info_parameter = get_info_field.base_resolver.info_parameter
        assert info_parameter is not None
        assert info_parameter.name == "info"


def test_custom_info_negative():
    """Test to ensure deprecation warning is emitted."""
    with pytest.warns(
        DeprecationWarning, match=r"Argument name-based matching of 'info'"
    ):

        @strawberry.field
        def get_info(info) -> bool:
            _ = info
            return True

        assert not get_info.arguments  # Should have no arguments matched

        info_parameter = get_info.base_resolver.info_parameter
        assert info_parameter is not None
        assert info_parameter.name == "info"


def test_type_equals_hash_repr():
    """Checks StrawberryType.equals/hash/repr"""

    global Value, A, B

    @strawberry.type
    class Value:
        query: str

    A = TypeVar("A")
    B = TypeVar("B")

    @strawberry.type
    class ObjectType:
        number: int
        number_optional: Optional[int]
        number_list: List[int]
        number_annotated: Annotated[int, "Hi"]
        value: Value
        value_optional: Optional[Value]
        value_list: List[Value]
        value_annotated: Annotated[Value, "Hi"]

        ref_number: "int"
        ref_number_optional: "Optional[int]"
        ref_number_list: "List[int]"
        ref_number_annotated: 'Annotated[int, "Hi"]'
        ref_value: "Value"
        ref_value_optional: "Optional[Value]"
        ref_value_list: "List[Value]"
        ref_value_annotated: 'Annotated[Value, "Hi"]'

        a: A
        ref_a: "A"
        b: B
        ref_b: "B"

    fields = {}
    for field in ObjectType._type_definition.fields:
        type_annotation = field.type_annotation

        # Assert that strawberryAnnotation.resolve() == strawberryAnnotation
        assert type_annotation == type_annotation.resolve()
        assert type_annotation.resolve() == type_annotation
        assert hash(type_annotation) == hash(type_annotation.resolve())

        fields[field.python_name] = field.type

    type_matrix = {
        "<class 'int'>": [
            fields["number"],
            fields["number_optional"].of_type,
            fields["number_list"].of_type,
            fields["number_annotated"].of_type,
            fields["ref_number"],
            fields["ref_number_optional"].of_type,
            fields["ref_number_list"].of_type,
            fields["ref_number_annotated"].of_type,
        ],
        "StrawberryOptional[int]": [
            fields["number_optional"],
            fields["ref_number_optional"],
        ],
        "StrawberryList[int]": [
            fields["number_list"],
            fields["ref_number_list"],
        ],
        "StrawberryAnnotated[int, 'Hi']": [
            fields["number_annotated"],
            fields["ref_number_annotated"],
        ],
        "<class 'test_argument_types.Value'>": [
            fields["value"],
            fields["value_optional"].of_type,
            fields["value_list"].of_type,
            fields["value_annotated"].of_type,
            fields["ref_value"],
            fields["ref_value_optional"].of_type,
            fields["ref_value_list"].of_type,
            fields["ref_value_annotated"].of_type,
        ],
        "StrawberryOptional[Value]": [
            fields["value_optional"],
            fields["ref_value_optional"],
        ],
        "StrawberryList[Value]": [
            fields["value_list"],
            fields["ref_value_list"],
        ],
        "StrawberryAnnotated[Value, 'Hi']": [
            fields["value_annotated"],
            fields["ref_value_annotated"],
        ],
        "StrawberryTypeVar[A]": [
            fields["a"],
            fields["ref_a"],
        ],
        "StrawberryTypeVar[B]": [
            fields["b"],
            fields["ref_b"],
        ],
    }

    # Tests all type permutations to check if they equals only when expected
    for group1, group1_types in type_matrix.items():
        for group2, group2_types in type_matrix.items():
            for type1 in group1_types:
                assert group1 == repr(type1)
                for type2 in group2_types:
                    if group1 == group2:
                        assert type1 == type2
                        assert hash(type1) == hash(type2)
                    else:
                        assert type1 != type2

    del Value, A, B
