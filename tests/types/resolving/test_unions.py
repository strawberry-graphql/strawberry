import sys
from typing import Generic, TypeVar, Union
from typing_extensions import Annotated

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import InvalidUnionTypeError
from strawberry.union import StrawberryUnion, union


def test_python_union():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    annotation = StrawberryAnnotation(Union[User, Error])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.types == (User, Error)

    assert resolved == StrawberryUnion(
        name=None,
        type_annotations=(StrawberryAnnotation(User), StrawberryAnnotation(Error)),
    )
    assert resolved == Union[User, Error]


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="short syntax for union is only available on python 3.10+",
)
def test_python_union_short_syntax():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    annotation = StrawberryAnnotation(User | Error)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.types == (User, Error)

    assert resolved == StrawberryUnion(
        name=None,
        type_annotations=(StrawberryAnnotation(User), StrawberryAnnotation(Error)),
    )
    assert resolved == Union[User, Error]


def test_strawberry_union():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    cool_union = Annotated[Union[User, Error], union(name="CoolUnion")]
    annotation = StrawberryAnnotation(cool_union)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.types == (User, Error)

    assert resolved == StrawberryUnion(
        name="CoolUnion",
        type_annotations=(StrawberryAnnotation(User), StrawberryAnnotation(Error)),
    )
    assert resolved != Union[User, Error]  # Name will be different


def test_named_union_with_deprecated_api_using_types_parameter():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = Annotated[Union[A, B], union(name="Result")]

    annotation = StrawberryAnnotation(Result)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)
    assert resolved.graphql_name == "Result"
    assert resolved.types == (A, B)


def test_union_with_generic_with_deprecated_api_using_types_parameter():
    T = TypeVar("T")

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    Result = strawberry.union("Result", types=(Error, Edge[str]))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.graphql_name == "Result"
    assert strawberry_union.types[0] == Error

    assert strawberry_union.types[1].__strawberry_definition__.is_generic is False


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `int` cannot be used in a GraphQL Union"
)
def test_error_with_scalar_types():
    Something = Annotated[
        Union[
            int,
            str,
            float,
            bool,
        ],
        strawberry.union("Something"),
    ]

    annotation = StrawberryAnnotation(Something)
    annotation.resolve()


# @pytest.mark.raises_strawberry_exception(
# def test_error_with_custom_scalar_types():


# @pytest.mark.raises_strawberry_exception(
# def test_error_with_non_strawberry_type():
#     @dataclass
#     class A:
