import asyncio
import typing

from graphql import GraphQLError

import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Query:
    hello: str = "strawberry"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def echo(
        self, message: str, delay: float = 0
    ) -> typing.AsyncGenerator[str, None]:
        await asyncio.sleep(delay)
        yield message

    @strawberry.subscription
    async def infinity(self, message: str) -> typing.AsyncGenerator[str, None]:
        while True:
            yield message
            await asyncio.sleep(1)

    @strawberry.subscription
    async def context(self, info) -> typing.AsyncGenerator[str, None]:
        yield info.context["custom_value"]

    @strawberry.subscription
    async def error(self, message: str) -> typing.AsyncGenerator[str, None]:
        yield GraphQLError(message)  # type: ignore

    @strawberry.subscription
    async def exception(self, message: str) -> typing.AsyncGenerator[str, None]:
        raise ValueError(message)

        # Without this yield, the method is not recognised as an async generator
        yield "Hi"  # noqa


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
