"""Common code shared across documentation."""
import typing

import strawberry


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"


schema = strawberry.Schema(query=Query)

modules = {
    "typing": typing,
    "strawberry": strawberry,
    "Book": Book,
    "Query": Query,
    "schema": schema,
}
