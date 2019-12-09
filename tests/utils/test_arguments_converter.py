import typing
from enum import Enum

import strawberry
from strawberry.utils.arguments import convert_args


def test_simple_types():
    args = {"integer": 1, "string": "abc", "float": 1.2, "bool": True}

    annotations = {"integer": int, "string": str, "float": float, "bool": bool}

    assert convert_args(args, annotations) == {
        "integer": 1,
        "string": "abc",
        "float": 1.2,
        "bool": True,
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
        say_hello_to: str
        was: int = strawberry.field(name="having", is_input=True)
        fun: str = strawberry.field(is_input=True)

    args = {
        "input": {"abc": "example", "sayHelloTo": "Patrick", "having": 10, "fun": "yes"}
    }

    annotations = {"input": MyInput}

    assert convert_args(args, annotations) == {
        "input": MyInput(abc="example", say_hello_to="Patrick", was=10, fun="yes")
    }


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


def test_optional_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input_list": [{"abc": "example"}]}

    annotations = {"input_list": typing.Optional[typing.List[MyInput]]}

    assert convert_args(args, annotations) == {"input_list": [MyInput(abc="example")]}


def test_nested_input_types():
    @strawberry.enum
    class ChangeType(Enum):
        MAJOR = "major"
        MINOR = "minor"
        PATCH = "patch"

    @strawberry.input
    class ReleaseInfo:
        change_type: ChangeType
        changelog: str

    @strawberry.enum
    class ReleaseFileStatus(Enum):
        MISSING = "missing"
        INVALID = "invalid"
        OK = "ok"

    @strawberry.input
    class AddReleaseFileCommentInput:
        pr_number: int
        status: ReleaseFileStatus
        release_info: typing.Optional[ReleaseInfo]

    args = {
        "input": {
            "prNumber": 12,
            "status": ReleaseFileStatus.OK.value,
            "releaseInfo": {
                "changeType": ChangeType.MAJOR.value,
                "changelog": "example",
            },
        }
    }

    annotations = {"input": AddReleaseFileCommentInput}

    assert convert_args(args, annotations) == {
        "input": AddReleaseFileCommentInput(
            pr_number=12,
            status=ReleaseFileStatus.OK,
            release_info=ReleaseInfo(change_type=ChangeType.MAJOR, changelog="example"),
        )
    }

    args = {
        "input": {
            "prNumber": 12,
            "status": ReleaseFileStatus.OK.value,
            "releaseInfo": None,
        }
    }

    annotations = {"input": AddReleaseFileCommentInput}

    assert convert_args(args, annotations) == {
        "input": AddReleaseFileCommentInput(
            pr_number=12, status=ReleaseFileStatus.OK, release_info=None
        )
    }


def test_nested_list_of_complex_types():
    @strawberry.input
    class Number:
        value: int

    @strawberry.input
    class Input:
        numbers: typing.List[Number]

    args = {"input": {"numbers": [{"value": 1}, {"value": 2}]}}

    annotations = {"input": Input}

    assert convert_args(args, annotations) == {
        "input": Input(numbers=[Number(1), Number(2)])
    }
