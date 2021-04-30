import sys
from typing import List, Optional

import pytest

import strawberry
from strawberry.type import StrawberryList, StrawberryOptional


def test_basic_list():
    @strawberry.type
    class Query:
        names: List[str]

    definition = Query._type_definition
    assert definition.name == "Query"
    
    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is str


def test_optional_list():
    @strawberry.type
    class Query:
        names: Optional[List[str]]

    definition = Query._type_definition
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is str


def test_list_of_optional():
    @strawberry.type
    class Query:
        names: List[Optional[str]]

    definition = Query._type_definition

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type is str


def test_optional_list_of_optional():
    @strawberry.type
    class Query:
        names: Optional[List[Optional[str]]]

    definition = Query._type_definition

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is str


def test_list_of_lists():
    @strawberry.type
    class Query:
        names: List[List[str]]

    definition = Query._type_definition

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.graphql_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is str


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
