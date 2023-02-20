import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: typing.Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"


schema = strawberry.Schema(Query)
