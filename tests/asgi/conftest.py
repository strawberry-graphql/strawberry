import asyncio
import typing
from enum import Enum
from typing import Optional, Union

import pytest

from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from graphql import GraphQLError

import strawberry
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.asgi.test import GraphQLTestClient
from strawberry.file_uploads import Upload
from strawberry.permission import BasePermission
from strawberry.types import Info


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return False


@strawberry.enum
class Flavor(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


@strawberry.type
class DebugInfo:
    num_active_result_handlers: int


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: typing.Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self) -> Optional[str]:
        return "Hey"

    @strawberry.field
    def root_name(root) -> str:
        return type(root).__name__


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_text(self, text_file: Upload) -> str:
        return (await text_file.read()).decode()

    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode()
            contents.append(content)
        return contents

    @strawberry.mutation
    async def read_folder(self, folder: FolderInput) -> typing.List[str]:
        contents = []
        for file in folder.files:
            content = (await file.read()).decode()
            contents.append(content)
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
            task for task in request.state.tasks.values() if not task.done()
        ]
        yield DebugInfo(num_active_result_handlers=len(active_result_handlers))


class GraphQL(BaseGraphQL):
    async def get_root_value(self, request):
        return Query()

    async def get_context(
        self,
        request: Union[Request, WebSocket],
        response: Optional[Response] = None,
    ):
        return {"request": request, "response": response, "custom_value": "Hi"}


@pytest.fixture
def schema():
    return strawberry.Schema(Query, mutation=Mutation, subscription=Subscription)


@pytest.fixture
def test_client(schema):
    app = GraphQL(schema)

    return TestClient(app)


@pytest.fixture
def graphql_client(test_client):
    yield GraphQLTestClient(test_client)


@pytest.fixture
def test_client_keep_alive(schema):
    app = GraphQL(schema, keep_alive=True, keep_alive_interval=0.1)

    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql(schema):
    app = GraphQL(schema, graphiql=False)

    return TestClient(app)
