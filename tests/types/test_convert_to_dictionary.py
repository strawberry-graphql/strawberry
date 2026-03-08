from enum import Enum

import strawberry
from strawberry import UNSET, asdict
from strawberry.types.maybe import Some


def test_convert_simple_type_to_dictionary():
    @strawberry.type
    class People:
        name: str
        age: int

    lorem = People(name="Alex", age=30)

    assert asdict(lorem) == {
        "name": "Alex",
        "age": 30,
    }


def test_convert_complex_type_to_dictionary():
    @strawberry.enum
    class Count(Enum):
        TWO = "two"
        FOUR = "four"

    @strawberry.type
    class Animal:
        legs: Count

    @strawberry.type
    class People:
        name: str
        animals: list[Animal]

    lorem = People(
        name="Kevin", animals=[Animal(legs=Count.TWO), Animal(legs=Count.FOUR)]
    )

    assert asdict(lorem) == {
        "name": "Kevin",
        "animals": [
            {"legs": Count.TWO},
            {"legs": Count.FOUR},
        ],
    }


def test_convert_input_to_dictionary():
    @strawberry.input
    class QnaInput:
        title: str
        description: str
        tags: list[str] | None = strawberry.field(default=None)

    title = "Where is the capital of United Kingdom?"
    description = "London is the capital of United Kingdom."
    qna = QnaInput(title=title, description=description)

    assert asdict(qna) == {
        "title": title,
        "description": description,
        "tags": None,
    }


def test_convert_some_values_are_unwrapped():
    @strawberry.type
    class User:
        name: str
        age: strawberry.Maybe[int]

    user = User(name="Alex", age=Some(30))

    assert asdict(user) == {
        "name": "Alex",
        "age": 30,
    }


def test_convert_unset_fields_are_excluded():
    @strawberry.input
    class UserInput:
        name: str
        age: int | None = UNSET

    user = UserInput(name="Alex")

    assert asdict(user) == {
        "name": "Alex",
    }


def test_convert_some_none_is_preserved():
    @strawberry.type
    class User:
        name: str
        age: strawberry.Maybe[int]

    user = User(name="Alex", age=Some(None))

    assert asdict(user) == {
        "name": "Alex",
        "age": None,
    }


def test_convert_nested_some_values():
    @strawberry.type
    class Address:
        city: str

    @strawberry.type
    class User:
        name: str
        address: strawberry.Maybe[Address]

    user = User(name="Alex", address=Some(Address(city="NYC")))

    assert asdict(user) == {
        "name": "Alex",
        "address": {"city": "NYC"},
    }
