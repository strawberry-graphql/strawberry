from typing import Annotated

import strawberry


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


# Union types using Annotated syntax
Union1 = Annotated[Foo | Bar | Baz | Qux, strawberry.union("Union1")]
Union2 = Annotated[Baz | Qux, strawberry.union("Union2")]
