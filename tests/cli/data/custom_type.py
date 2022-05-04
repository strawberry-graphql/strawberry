import typing

import strawberry


@strawberry.type
class Query:
    a: 'MyType'

@strawberry.type
class MyType:
    b: typing.Optional[str]
    c: int
