from typing import Optional, TypeVar

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import (
    StrawberryList,
    StrawberryOptional,
    StrawberryTypeVar,
)


def test_basic_string():
    annotation = StrawberryAnnotation("str")
    resolved = annotation.resolve()

    assert resolved is str


def test_list_of_string():
    annotation = StrawberryAnnotation(list["int"])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is int

    assert resolved == StrawberryList(of_type=int)
    assert resolved == list[int]


def test_list_of_string_of_type():
    @strawberry.type
    class NameGoesHere:
        foo: bool

    annotation = StrawberryAnnotation(list["NameGoesHere"], namespace=locals())
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is NameGoesHere

    assert resolved == StrawberryList(of_type=NameGoesHere)
    assert resolved == list[NameGoesHere]


def test_optional_of_string():
    annotation = StrawberryAnnotation(Optional["bool"])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is bool

    assert resolved == StrawberryOptional(of_type=bool)
    assert resolved == Optional[bool]


def test_string_of_object():
    @strawberry.type
    class StrType:
        thing: int

    annotation = StrawberryAnnotation("StrType", namespace=locals())
    resolved = annotation.resolve()

    assert resolved is StrType


def test_string_of_type_var():
    T = TypeVar("T")

    annotation = StrawberryAnnotation("T", namespace=locals())
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryTypeVar)
    assert resolved.type_var is T

    assert resolved == T


def test_string_of_list():
    namespace = {**locals(), **globals()}

    annotation = StrawberryAnnotation("list[float]", namespace=namespace)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is float

    assert resolved == StrawberryList(of_type=float)
    assert resolved == list[float]


def test_string_of_list_of_type():
    @strawberry.type
    class BlahBlah:
        foo: bool

    namespace = {**locals(), **globals()}

    annotation = StrawberryAnnotation("list[BlahBlah]", namespace=namespace)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is BlahBlah

    assert resolved == StrawberryList(of_type=BlahBlah)
    assert resolved == list[BlahBlah]


def test_string_of_optional():
    namespace = {**locals(), **globals()}

    annotation = StrawberryAnnotation("Optional[int]", namespace=namespace)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type is int

    assert resolved == StrawberryOptional(of_type=int)
    assert resolved == Optional[int]


# TODO: Move to object tests to test namespace logic
def test_basic_types():
    @strawberry.type
    class Query:
        name: "str"
        age: "int"

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert field1.type is str

    assert field2.python_name == "age"
    assert field2.type is int


# TODO: Move to object tests to test namespace logic
def test_optional():
    @strawberry.type
    class Query:
        name: "Optional[str]"
        age: "Optional[int]"

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert field1.type.of_type is str

    assert field2.python_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is int


# TODO: Move to object tests to test namespace logic
def test_basic_list():
    @strawberry.type
    class Query:
        names: "list[str]"

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "names"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is str


# TODO: Move to object tests to test namespace logic
def test_list_of_types():
    global User

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        users: "list[User]"

    definition = Query.__strawberry_definition__
    assert definition.name == "Query"

    [field] = definition.fields

    assert field.python_name == "users"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is User

    del User
