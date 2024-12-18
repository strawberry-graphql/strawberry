from typing import Optional, Union

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import StrawberryOptional
from strawberry.types.unset import UnsetType


def test_basic_optional():
    annotation = StrawberryAnnotation(Optional[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is str

    assert resolved == StrawberryOptional(of_type=str)
    assert resolved == Optional[str]


def test_optional_with_unset():
    annotation = StrawberryAnnotation(Union[UnsetType, Optional[str]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is str

    assert resolved == StrawberryOptional(of_type=str)
    assert resolved == Optional[str]


def test_optional_with_unset_as_union():
    annotation = StrawberryAnnotation(Union[UnsetType, None, str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is str

    assert resolved == StrawberryOptional(of_type=str)
    assert resolved == Optional[str]


def test_optional_list():
    annotation = StrawberryAnnotation(Optional[list[bool]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type == list[bool]

    assert resolved == StrawberryOptional(of_type=list[bool])
    assert resolved == Optional[list[bool]]


def test_optional_optional():
    """Optional[Optional[...]] is squashed by Python to just Optional[...]"""
    annotation = StrawberryAnnotation(Optional[Optional[bool]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is bool

    assert resolved == StrawberryOptional(of_type=bool)
    assert resolved == Optional[Optional[bool]]
    assert resolved == Optional[bool]


def test_optional_union():
    @strawberry.type
    class CoolType:
        foo: float

    @strawberry.type
    class UncoolType:
        bar: bool

    annotation = StrawberryAnnotation(Optional[Union[CoolType, UncoolType]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type == Union[CoolType, UncoolType]

    assert resolved == StrawberryOptional(of_type=Union[CoolType, UncoolType])
    assert resolved == Optional[Union[CoolType, UncoolType]]


# TODO: move to a field test file
def test_type_add_type_definition_with_fields():
    @strawberry.type
    class Query:
        name: Optional[str]
        age: Optional[int]

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert field1.graphql_name is None
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.python_name == "age"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


# TODO: move to a field test file
def test_passing_custom_names_to_fields():
    @strawberry.type
    class Query:
        x: Optional[str] = strawberry.field(name="name")
        y: Optional[int] = strawberry.field(name="age")

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.python_name == "x"
    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.python_name == "y"
    assert field2.graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


# TODO: move to a field test file
def test_passing_nothing_to_fields():
    @strawberry.type
    class Query:
        name: Optional[str] = strawberry.field()
        age: Optional[int] = strawberry.field()

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert field1.graphql_name is None
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.python_name == "age"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


# TODO: move to a resolver test file
def test_resolver_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> Optional[str]:
            return "Name"

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "name"
    assert field.graphql_name is None
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is str


# TODO: move to a resolver test file
def test_resolver_fields_arguments():
    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, argument: Optional[str]) -> Optional[str]:
            return "Name"

    definition = Query.__strawberry_definition__

    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "name"
    assert field.graphql_name is None
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is str

    [argument] = field.arguments

    assert argument.python_name == "argument"
    assert argument.graphql_name is None
    assert isinstance(argument.type, StrawberryOptional)
    assert argument.type.of_type is str
