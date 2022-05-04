import typing

import strawberry


@strawberry.type
class Query:
    non_nullable: typing.List[str]
    both_nullable: typing.Optional[typing.List[typing.Optional[str]]]
    list_can_be_null: typing.Optional[typing.List[str]]
    list_can_never_be_null: typing.List[typing.Optional[str]]
