import sys
from dataclasses import dataclass
from typing import Generic, NewType, TypeVar, Union

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


def test_named_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.graphql_name == "Result"
    assert strawberry_union.types == (A, B)


def test_union_with_generic():
    T = TypeVar("T")

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    Result = strawberry.union("Result", (Error, Edge[str]))

    strawberry_union = Result
    assert isinstance(strawberry_union, StrawberryUnion)
    assert strawberry_union.graphql_name == "Result"
    assert strawberry_union.types[0] == Error

    assert strawberry_union.types[1].__strawberry_definition__.is_generic is False


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
