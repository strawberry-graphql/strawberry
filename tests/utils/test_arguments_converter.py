from enum import Enum
from typing import List, Optional

import strawberry
from strawberry.arguments import UNSET, StrawberryArgument, convert_arguments


def test_simple_types():
    args = {"integer": 1, "string": "abc", "float": 1.2, "bool": True}

    arguments = [
        StrawberryArgument(graphql_name="integer", type_=int, python_name="integer"),
        StrawberryArgument(graphql_name="string", type_=str, python_name="string"),
        StrawberryArgument(graphql_name="float", type_=float, python_name="float"),
        StrawberryArgument(graphql_name="bool", type_=bool, python_name="bool"),
    ]

    assert convert_arguments(args, arguments) == {
        "integer": 1,
        "string": "abc",
        "float": 1.2,
        "bool": True,
    }


def test_list():
    args = {
        "integerList": [1, 2],
        "stringList": ["abc", "cde"],
    }

    arguments = [
        StrawberryArgument(
            graphql_name="integerList",
            python_name="integer_list",
            type_=int,
            is_list=True,
            child=StrawberryArgument(graphql_name=None, python_name=None, type_=int),
        ),
        StrawberryArgument(
            graphql_name="stringList",
            python_name="string_list",
            type_=str,
            is_list=True,
            child=StrawberryArgument(graphql_name=None, python_name=None, type_=str),
        ),
    ]

    assert convert_arguments(args, arguments) == {
        "integer_list": [1, 2],
        "string_list": ["abc", "cde"],
    }


def test_input_types():
    @strawberry.input
    class MyInput:
        abc: str
        say_hello_to: str
        fun: str
        was: int = strawberry.field(name="having")

    args = {
        "input": {"abc": "example", "sayHelloTo": "Patrick", "having": 10, "fun": "yes"}
    }

    arguments = [
        StrawberryArgument(graphql_name=None, python_name="input", type_=MyInput)
    ]

    assert convert_arguments(args, arguments) == {
        "input": MyInput(abc="example", say_hello_to="Patrick", was=10, fun="yes")
    }


def test_optional_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input": {"abc": "example"}}

    arguments = [
        StrawberryArgument(
            graphql_name=None, python_name="input", type_=MyInput, is_optional=True
        )
    ]

    assert convert_arguments(args, arguments) == {"input": MyInput(abc="example")}


def test_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"inputList": [{"abc": "example"}]}

    arguments = [
        StrawberryArgument(
            graphql_name="inputList",
            python_name="input_list",
            type_=None,
            child=StrawberryArgument(
                graphql_name=None, python_name=None, type_=MyInput
            ),
            is_list=True,
        )
    ]

    assert convert_arguments(args, arguments) == {
        "input_list": [MyInput(abc="example")]
    }


def test_optional_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"inputList": [{"abc": "example"}]}

    arguments = [
        StrawberryArgument(
            graphql_name="inputList",
            python_name="input_list",
            is_optional=True,
            type_=None,
            child=StrawberryArgument(
                graphql_name=None, python_name=None, type_=MyInput
            ),
            is_list=True,
        )
    ]
    assert convert_arguments(args, arguments) == {
        "input_list": [MyInput(abc="example")]
    }


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
        release_info: Optional[ReleaseInfo]

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

    arguments = [
        StrawberryArgument(
            graphql_name=None, python_name="input", type_=AddReleaseFileCommentInput
        )
    ]

    assert convert_arguments(args, arguments) == {
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

    arguments = [
        StrawberryArgument(
            graphql_name=None, python_name="input", type_=AddReleaseFileCommentInput
        )
    ]

    assert convert_arguments(args, arguments) == {
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
        numbers: List[Number]

    args = {"input": {"numbers": [{"value": 1}, {"value": 2}]}}

    arguments = [
        StrawberryArgument(graphql_name=None, python_name="input", type_=Input)
    ]

    assert convert_arguments(args, arguments) == {
        "input": Input(numbers=[Number(1), Number(2)])
    }


def test_uses_default_for_optional_types_when_nothing_is_passed():
    @strawberry.input
    class Number:
        value: int

    @strawberry.input
    class Input:
        numbers: Optional[Number] = UNSET
        numbers_second: Optional[Number] = UNSET

    # case 1
    args = {"input": {}}

    arguments = [
        StrawberryArgument(graphql_name=None, python_name="input", type_=Input)
    ]

    assert convert_arguments(args, arguments) == {"input": Input(UNSET, UNSET)}

    # case 2
    args = {"input": {"numbersSecond": None}}

    arguments = [
        StrawberryArgument(graphql_name=None, python_name="input", type_=Input)
    ]

    assert convert_arguments(args, arguments) == {"input": Input(UNSET, None)}


def test_when_optional():
    @strawberry.input
    class Number:
        value: int

    @strawberry.input
    class Input:
        numbers: Optional[Number] = UNSET
        numbers_second: Optional[Number] = UNSET

    args = {}

    arguments = [
        StrawberryArgument(
            graphql_name=None, python_name="input", type_=Input, is_optional=True
        )
    ]

    assert convert_arguments(args, arguments) == {}
