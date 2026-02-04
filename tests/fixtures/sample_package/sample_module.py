from enum import Enum
from typing import Annotated, NewType

import strawberry
from strawberry.schema.config import StrawberryConfig

ExampleScalar = NewType("ExampleScalar", object)


@strawberry.type
class A:
    name: str


@strawberry.type
class B:
    a: A


UnionExample = Annotated[A | B, strawberry.union("UnionExample")]


class SampleClass:
    def __init__(self, schema):
        self.schema = schema


@strawberry.enum
class Role(Enum):
    ADMIN = "ADMIN"
    USER = "USER"


@strawberry.type
class User:
    name: str
    age: int
    role: Role
    example_scalar: ExampleScalar
    union_example: UnionExample
    inline_union: Annotated[A | B, strawberry.union("InlineUnion")]


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)


def create_schema():
    return strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                ExampleScalar: strawberry.scalar(
                    name="ExampleScalar",
                    serialize=lambda v: v,
                    parse_value=lambda v: v,
                )
            }
        ),
    )


schema = create_schema()
sample_instance = SampleClass(schema)
not_a_schema = 42
