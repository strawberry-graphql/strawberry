import sys
from typing import List, Optional

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.type import StrawberryList


def test_basic_list():

    annotation = StrawberryAnnotation(List[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == List[str]


def test_list_of_optional():
    annotation = StrawberryAnnotation(List[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == List[Optional[int]]


def test_list_of_lists():
    annotation = StrawberryAnnotation(List[List[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == List[float]

    assert resolved == StrawberryList(of_type=List[float])
    assert resolved == List[List[float]]


# TODO: Move to new test_builtin_annotations.py
@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="built-in generic annotations where added in python 3.9",
)
def test_list_of_lists_generic_annotations():
    @strawberry.type
    class Query:
        names: list[list[str]]

    definition = Query._type_definition

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is str
