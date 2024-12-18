from enum import Enum
from typing import Annotated, Optional

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import UnsupportedTypeError
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types.arguments import StrawberryArgument, convert_arguments
from strawberry.types.lazy_type import LazyType
from strawberry.types.unset import UNSET


def test_simple_types():
    args = {"integer": 1, "string": "abc", "float": 1.2, "bool": True}

    arguments = [
        StrawberryArgument(
            graphql_name="integer",
            type_annotation=StrawberryAnnotation(int),
            python_name="integer",
        ),
        StrawberryArgument(
            graphql_name="string",
            type_annotation=StrawberryAnnotation(str),
            python_name="string",
        ),
        StrawberryArgument(
            graphql_name="float",
            type_annotation=StrawberryAnnotation(float),
            python_name="float",
        ),
        StrawberryArgument(
            graphql_name="bool",
            type_annotation=StrawberryAnnotation(bool),
            python_name="bool",
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {
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
            type_annotation=StrawberryAnnotation(list[int]),
        ),
        StrawberryArgument(
            graphql_name="stringList",
            python_name="string_list",
            type_annotation=StrawberryAnnotation(list[str]),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {
        "integer_list": [1, 2],
        "string_list": ["abc", "cde"],
    }


@strawberry.input
class LaziestType:
    something: bool


def test_lazy():
    LazierType = LazyType["LaziestType", __name__]

    args = {
        "lazyArg": {"something": True},
    }

    arguments = [
        StrawberryArgument(
            graphql_name="lazyArg",
            python_name="lazy_arg",
            type_annotation=StrawberryAnnotation(LazierType),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"lazy_arg": LaziestType(something=True)}


def test_annotated():
    LazierType = Annotated["LaziestType", strawberry.lazy(__name__)]

    args = {
        "lazyArg": {"something": True},
    }

    arguments = [
        StrawberryArgument(
            graphql_name="lazyArg",
            python_name="lazy_arg",
            type_annotation=StrawberryAnnotation(LazierType),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"lazy_arg": LaziestType(something=True)}


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
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(MyInput),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input": MyInput(abc="example", say_hello_to="Patrick", was=10, fun="yes")}


def test_optional_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"input": {"abc": "example"}}

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Optional[MyInput]),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input": MyInput(abc="example")}


def test_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"inputList": [{"abc": "example"}]}

    arguments = [
        StrawberryArgument(
            graphql_name="inputList",
            python_name="input_list",
            type_annotation=StrawberryAnnotation(list[MyInput]),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input_list": [MyInput(abc="example")]}


def test_optional_list_of_input_types():
    @strawberry.input
    class MyInput:
        abc: str

    args = {"inputList": [{"abc": "example"}]}

    arguments = [
        StrawberryArgument(
            graphql_name="inputList",
            python_name="input_list",
            type_annotation=StrawberryAnnotation(Optional[list[MyInput]]),
        ),
    ]
    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input_list": [MyInput(abc="example")]}


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
            "status": ReleaseFileStatus.OK,
            "releaseInfo": {
                "changeType": ChangeType.MAJOR,
                "changelog": "example",
            },
        }
    }

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(AddReleaseFileCommentInput),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {
        "input": AddReleaseFileCommentInput(
            pr_number=12,
            status=ReleaseFileStatus.OK,
            release_info=ReleaseInfo(change_type=ChangeType.MAJOR, changelog="example"),
        )
    }

    args = {
        "input": {
            "prNumber": 12,
            "status": ReleaseFileStatus.OK,
            "releaseInfo": None,
        }
    }

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(AddReleaseFileCommentInput),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {
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
        numbers: list[Number]

    args = {"input": {"numbers": [{"value": 1}, {"value": 2}]}}

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Input),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input": Input(numbers=[Number(value=1), Number(value=2)])}


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
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Input),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input": Input(numbers=UNSET, numbers_second=UNSET)}

    # case 2
    args = {"input": {"numbersSecond": None}}

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Input),
        ),
    ]

    assert convert_arguments(
        args,
        arguments,
        scalar_registry=DEFAULT_SCALAR_REGISTRY,
        config=StrawberryConfig(),
    ) == {"input": Input(numbers=UNSET, numbers_second=None)}


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
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Optional[Input]),
        )
    ]

    assert (
        convert_arguments(
            args,
            arguments,
            scalar_registry=DEFAULT_SCALAR_REGISTRY,
            config=StrawberryConfig(),
        )
        == {}
    )


@pytest.mark.raises_strawberry_exception(
    UnsupportedTypeError,
    match=r"<class .*> conversion is not supported",
)
def test_fails_when_passing_non_strawberry_classes():
    class Input:
        numbers: list[int]

    args = {
        "input": {
            "numbers": [1, 2],
        }
    }

    arguments = [
        StrawberryArgument(
            graphql_name=None,
            python_name="input",
            type_annotation=StrawberryAnnotation(Optional[Input]),
        )
    ]

    assert (
        convert_arguments(
            args,
            arguments,
            scalar_registry=DEFAULT_SCALAR_REGISTRY,
            config=StrawberryConfig(),
        )
        == {}
    )
