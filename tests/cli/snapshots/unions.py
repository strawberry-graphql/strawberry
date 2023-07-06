from typing import Annotated

import strawberry

# create a few types and then a union type


@strawberry.type
class Foo:
    a: str


@strawberry.type
class Bar:
    b: str


@strawberry.type
class Baz:
    c: str


@strawberry.type
class Qux:
    d: str


# this is the union type

Union1 = Annotated[Foo | Bar | Baz | Qux, strawberry.union(name="Union1")]
Union2 = Annotated[Baz | Qux, strawberry.union(name="Union2")]
