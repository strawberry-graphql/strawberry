import sys
import typing
from typing import Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions.invalid_union_type import InvalidUnionTypeError
from strawberry.schema.types.base_scalars import Date, DateTime
from strawberry.types.base import StrawberryOptional
from strawberry.types.union import StrawberryUnion

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pipe syntax for union is only available on python 3.10+",
)


def test_union_short_syntax():
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


def test_union_none():
    @strawberry.type
    class User:
        name: str

    annotation = StrawberryAnnotation(User | None)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)
    assert resolved.of_type == User

    assert resolved == StrawberryOptional(
        of_type=User,
    )
    assert resolved == Union[User, None]


def test_strawberry_union_and_none():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    UserOrError = typing.Annotated[User | Error, strawberry.union(name="UserOrError")]
    annotation = StrawberryAnnotation(UserOrError | None)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)

    assert resolved == StrawberryOptional(
        of_type=StrawberryUnion(
            name="UserOrError",
            type_annotations=(StrawberryAnnotation(User), StrawberryAnnotation(Error)),
        )
    )


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError,
    match="Type `int` cannot be used in a GraphQL Union",
)
def test_raises_error_when_piping_with_scalar():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    UserOrError = typing.Annotated[User | Error, strawberry.union("UserOrError")]

    @strawberry.type
    class Query:
        user: UserOrError | int

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError,
    match="Type `date` cannot be used in a GraphQL Union",
)
def test_raises_error_when_piping_with_custom_scalar():
    StrawberryAnnotation(Date | DateTime)
