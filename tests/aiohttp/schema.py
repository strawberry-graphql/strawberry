import asyncio
import typing
from enum import Enum

from graphql import GraphQLError

import strawberry
from strawberry.file_uploads import Upload


@strawberry.enum
class Flavor(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class DebugInfo:
    num_active_result_handlers: int


@strawberry.type
class Query:
    hello: str = "strawberry"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()

    @strawberry.mutation
    def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            contents.append(file.read().decode())
        return contents

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> typing.List[str]:
        contents = []
        for file in folder.files:
            contents.append(file.read().decode())
        return contents


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

    @strawberry.subscription
    async def flavors(self) -> typing.AsyncGenerator[Flavor, None]:
        yield Flavor.VANILLA
        yield Flavor.STRAWBERRY
        yield Flavor.CHOCOLATE

    @strawberry.subscription
    async def debug(self, info) -> typing.AsyncGenerator[DebugInfo, None]:
        request = info.context["request"]
        active_result_handlers = [
            task for task in request["tasks"].values() if not task.done()
        ]
        yield DebugInfo(num_active_result_handlers=len(active_result_handlers))


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
