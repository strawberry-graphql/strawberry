from enum import Enum
from typing import Annotated, NewType, Union

import strawberry

ExampleScalar = strawberry.scalar(
    NewType("ExampleScalar", object),
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


@strawberry.type
class A:
    name: str


@strawberry.type
class B:
    a: A


UnionExample = Annotated[Union[A, B], strawberry.union("UnionExample")]


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
    inline_union: Annotated[Union[A, B], strawberry.union("InlineUnion")]


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)


def create_schema():
    return strawberry.Schema(query=Query)


schema = create_schema()
sample_instance = SampleClass(schema)
not_a_schema = 42
