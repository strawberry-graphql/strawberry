import typing

import strawberry


@strawberry.type
class Query:
    old: typing.Optional[str] = strawberry.field(
        deprecation_reason='Replaced by `new` field',
    )
    new: str
