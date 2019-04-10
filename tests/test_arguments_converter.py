import typing

import strawberry
from strawberry.field import convert_args


def test_simple_types():
    args = {"integer": 1, "string": "abc", "float": 1.2}

    annotations = {"integer": int, "string": str, "float": float}

    assert convert_args(args, annotations) == {
        "integer": 1,
        "string": "abc",
        "float": 1.2,
    }


def test_list():
    args = {
        "integer_list": [1, 2],
        "string_list": ["abc", "cde"],
        "float_list": [1.2, 2.3],
    }

    annotations = {
        "integer_list": typing.List[int],
        "string_list": typing.List[str],
        "float_list": typing.List[float],
    }

    assert convert_args(args, annotations) == {
        "integer_list": [1, 2],
        "string_list": ["abc", "cde"],
        "float_list": [1.2, 2.3],
    }


def test_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input": {"abc": "example"}}

    annotations = {"input": MyInput}

    assert convert_args(args, annotations) == {"input": MyInput(abc="example")}


def test_optional_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input": {"abc": "example"}}

    annotations = {"input": typing.Optional[MyInput]}

    assert convert_args(args, annotations) == {"input": MyInput(abc="example")}


def test_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input_list": [{"abc": "example"}]}

    annotations = {"input_list": typing.List[MyInput]}

    assert convert_args(args, annotations) == {"input_list": [MyInput(abc="example")]}
