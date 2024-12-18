from enum import Enum
from typing import Optional

import strawberry
from strawberry import asdict


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
        tags: Optional[list[str]] = strawberry.field(default=None)

    title = "Where is the capital of United Kingdom?"
    description = "London is the capital of United Kingdom."
    qna = QnaInput(title=title, description=description)

    assert asdict(qna) == {
        "title": title,
        "description": description,
        "tags": None,
    }
