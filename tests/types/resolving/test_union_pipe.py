import sys
from typing import Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import InvalidUnionType
from strawberry.type import StrawberryOptional
from strawberry.union import StrawberryUnion


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

    UserOrError = strawberry.union("UserOrError", (User, Error))
    annotation = StrawberryAnnotation(UserOrError | None)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryOptional)

    assert resolved == StrawberryOptional(
        of_type=StrawberryUnion(
            name="UserOrError",
            type_annotations=(StrawberryAnnotation(User), StrawberryAnnotation(Error)),
        )
    )


def test_strawberry_union_and_another_type():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Example:
        name: str

    UserOrError = strawberry.union("UserOrError", (User, Error))
    annotation = StrawberryAnnotation(UserOrError | Example)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)

    assert resolved == StrawberryUnion(
        type_annotations=(
            StrawberryAnnotation(User),
            StrawberryAnnotation(Error),
            StrawberryAnnotation(Example),
        ),
    )


def test_strawberry_union_and_another_strawberry_union():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Example:
        name: str

    UserOrError = strawberry.union("UserOrError", (User, Error))
    ExampleOrError = strawberry.union("ExampleOrError", (Example, Error))
    annotation = StrawberryAnnotation(UserOrError | ExampleOrError)
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)

    assert len(resolved.type_annotations) == 3

    # doing this to avoid errors due to order of types
    assert StrawberryAnnotation(User) in resolved.type_annotations
    assert StrawberryAnnotation(Error) in resolved.type_annotations
    assert StrawberryAnnotation(Example) in resolved.type_annotations


def test_strawberry_union_and_a_union():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class Example:
        name: str

    UserOrError = strawberry.union("UserOrError", (User, Error))
    annotation = StrawberryAnnotation(UserOrError | Union[Example, Error])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryUnion)

    assert len(resolved.type_annotations) == 3

    # doing this to avoid errors due to order of types
    assert StrawberryAnnotation(User) in resolved.type_annotations
    assert StrawberryAnnotation(Error) in resolved.type_annotations
    assert StrawberryAnnotation(Example) in resolved.type_annotations


def test_raises_error_when_piping_with_scalar():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    UserOrError = strawberry.union("UserOrError", (User, Error))

    with pytest.raises(InvalidUnionType):
        StrawberryAnnotation(UserOrError | int)
