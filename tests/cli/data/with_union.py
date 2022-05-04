import typing

import strawberry


@strawberry.type
class Query:
    attempt: 'Attempt' = strawberry.field(
        description="""Was my attempt successful?""",
    )

@strawberry.type
class Success:
    data: typing.Optional[str]

@strawberry.type
class Failure:
    error: typing.Optional[str]

Attempt = strawberry.union(
    'Attempt',
    (Success, Failure),
)
