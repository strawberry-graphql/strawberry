import sys
from typing import List, Optional

import pytest

import strawberry


def test_basic_list():
    @strawberry.type
    class Query:
        names: List[str]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False


def test_optional_list():
    @strawberry.type
    class Query:
        names: Optional[List[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False


def test_list_of_optional():
    @strawberry.type
    class Query:
        names: List[Optional[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional


def test_optional_list_of_optional():
    @strawberry.type
    class Query:
        names: Optional[List[Optional[str]]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional


def test_list_of_lists():
    @strawberry.type
    class Query:
        names: List[List[str]]

    definition = Query._type_definition

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type is None
    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional is False
    assert definition.fields[0].child.child.type == str
    assert definition.fields[0].child.child.is_optional is False


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
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "names"
    assert definition.fields[0].is_list
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].child.type is None
    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional is False
    assert definition.fields[0].child.child.type == str
    assert definition.fields[0].child.child.is_optional is False
