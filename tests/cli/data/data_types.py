import typing

import strawberry


@strawberry.type
class Query:
    string: str
    stringop: typing.Optional[str]
    int: int
    intop: typing.Optional[int]
    boolean: bool
    booleanop: typing.Optional[bool]
    float: float
    floatop: typing.Optional[float]
    id: strawberry.ID
    with_description: typing.Optional[str] = strawberry.field(
        description='''My description''',
    )
    with_multiline_description: str = strawberry.field(
        description='''With multiline
description''',
    )
