from dataclasses import dataclass
from typing import Generic, NewType, TypeVar, Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import InvalidUnionTypeError
from strawberry.types.union import StrawberryUnion, union

pytestmark = pytest.mark.filterwarnings(
    "ignore:Passing types to `strawberry.union` is deprecated."
)


def test_strawberry_union():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    cool_union = union(name="CoolUnion", types=(User, Error))
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

    Result = strawberry.union("Result", types=(A, B))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.graphql_name == "Result"
    assert strawberry_union.types == (A, B)


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

    assert (
        strawberry_union.types[1].__strawberry_definition__.is_graphql_generic is False
    )


def test_cannot_use_union_directly():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    with pytest.raises(ValueError, match=r"Cannot use union type directly"):
        Result()  # type: ignore


def test_error_with_empty_type_list():
    with pytest.raises(TypeError, match="No types passed to `union`"):
        strawberry.union("Result", ())


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `int` cannot be used in a GraphQL Union"
)
def test_error_with_scalar_types():
    strawberry.union(
        "Result",
        (
            int,
            str,
            float,
            bool,
        ),
    )


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `CustomScalar` cannot be used in a GraphQL Union"
)
def test_error_with_custom_scalar_types():
    CustomScalar = strawberry.scalar(
        NewType("CustomScalar", str),
        serialize=lambda v: str(v),
        parse_value=lambda v: str(v),
    )

    strawberry.union("Result", (CustomScalar,))


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `A` cannot be used in a GraphQL Union"
)
def test_error_with_non_strawberry_type():
    @dataclass
    class A:
        a: int

    strawberry.union("Result", (A,))
