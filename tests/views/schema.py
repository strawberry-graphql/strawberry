import asyncio
import contextlib
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Any, Optional, Union

from graphql import GraphQLError

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.file_uploads import Upload
from strawberry.permission import BasePermission
from strawberry.subscriptions.protocols.graphql_transport_ws.types import PingMessage
from strawberry.types import ExecutionContext


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


class MyExtension(SchemaExtension):
    def get_results(self) -> dict[str, str]:
        return {"example": "example"}


def _read_file(text_file: Upload) -> str:
    with contextlib.suppress(ModuleNotFoundError):
        from starlette.datastructures import UploadFile

        # allow to keep this function synchronous, starlette's files have
        # async methods for reading
        if isinstance(text_file, UploadFile):
            text_file = text_file.file._file  # type: ignore

    with contextlib.suppress(ModuleNotFoundError):
        from litestar.datastructures import UploadFile as LitestarUploadFile

        if isinstance(text_file, LitestarUploadFile):
            text_file = text_file.file  # type: ignore

    return text_file.read().decode()


@strawberry.enum
class Flavor(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


@strawberry.input
class FolderInput:
    files: list[Upload]


@strawberry.type
class DebugInfo:
    num_active_result_handlers: int
    is_connection_init_timeout_task_done: Optional[bool]


@strawberry.type
class Query:
    @strawberry.field
    def greetings(self) -> str:
        return "hello"

    @strawberry.field
    def hello(self, name: Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field
    async def async_hello(self, name: Optional[str] = None, delay: float = 0) -> str:
        await asyncio.sleep(delay)
        return f"Hello {name or 'world'}"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self) -> Optional[str]:
        return "Hey"

    @strawberry.field
    async def error(self, message: str) -> AsyncGenerator[str, None]:
        yield GraphQLError(message)  # type: ignore

    @strawberry.field
    async def exception(self, message: str) -> str:
        raise ValueError(message)

    @strawberry.field
    def teapot(self, info: strawberry.Info[Any, None]) -> str:
        info.context["response"].status_code = 418

        return "🫖"

    @strawberry.field
    def root_name(self) -> str:
        return type(self).__name__

    @strawberry.field
    def value_from_context(self, info: strawberry.Info) -> str:
        return info.context["custom_value"]

    @strawberry.field
    def returns_401(self, info: strawberry.Info) -> str:
        response = info.context["response"]
        if hasattr(response, "set_status"):
            response.set_status(401)
        else:
            response.status_code = 401

        return "hey"

    @strawberry.field
    def set_header(self, info: strawberry.Info, name: str) -> str:
        response = info.context["response"]
        response.headers["X-Name"] = name

        return name


@strawberry.type
class Mutation:
    @strawberry.mutation
    def echo(self, string_to_echo: str) -> str:
        return string_to_echo

    @strawberry.mutation
    def hello(self) -> str:
        return "strawberry"

    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return _read_file(text_file)

    @strawberry.mutation
    def read_files(self, files: list[Upload]) -> list[str]:
        return list(map(_read_file, files))

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> list[str]:
        return list(map(_read_file, folder.files))

    @strawberry.mutation
    def match_text(self, text_file: Upload, pattern: str) -> str:
        text = text_file.read().decode()
        return pattern if pattern in text else ""


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def echo(self, message: str, delay: float = 0) -> AsyncGenerator[str, None]:
        await asyncio.sleep(delay)
        yield message

    @strawberry.subscription
    async def request_ping(self, info: strawberry.Info) -> AsyncGenerator[bool, None]:
        ws = info.context["ws"]
        await ws.send_json(PingMessage({"type": "ping"}))
        yield True

    @strawberry.subscription
    async def infinity(self, message: str) -> AsyncGenerator[str, None]:
        while True:
            yield message
            await asyncio.sleep(1)

    @strawberry.subscription
    async def context(self, info: strawberry.Info) -> AsyncGenerator[str, None]:
        yield info.context["custom_value"]

    @strawberry.subscription
    async def error(self, message: str) -> AsyncGenerator[str, None]:
        yield GraphQLError(message)  # type: ignore

    @strawberry.subscription
    async def exception(self, message: str) -> AsyncGenerator[str, None]:
        raise ValueError(message)

        # Without this yield, the method is not recognised as an async generator
        yield "Hi"

    @strawberry.subscription
    async def flavors(self) -> AsyncGenerator[Flavor, None]:
        yield Flavor.VANILLA
        yield Flavor.STRAWBERRY
        yield Flavor.CHOCOLATE

    @strawberry.subscription
    async def flavors_invalid(self) -> AsyncGenerator[Flavor, None]:
        yield Flavor.VANILLA
        yield "invalid type"  # type: ignore
        yield Flavor.CHOCOLATE

    @strawberry.subscription
    async def debug(self, info: strawberry.Info) -> AsyncGenerator[DebugInfo, None]:
        active_result_handlers = [
            task for task in info.context["get_tasks"]() if not task.done()
        ]

        connection_init_timeout_task = info.context["connectionInitTimeoutTask"]
        is_connection_init_timeout_task_done = (
            connection_init_timeout_task.done()
            if connection_init_timeout_task
            else None
        )

        yield DebugInfo(
            num_active_result_handlers=len(active_result_handlers),
            is_connection_init_timeout_task_done=is_connection_init_timeout_task_done,
        )

    @strawberry.subscription
    async def listener(
        self,
        info: strawberry.Info,
        timeout: Optional[float] = None,
        group: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        yield info.context["request"].channel_name

        async with info.context["request"].listen_to_channel(
            type="test.message",
            timeout=timeout,
            groups=[group] if group is not None else [],
        ) as cm:
            async for message in cm:
                yield message["text"]

    @strawberry.subscription
    async def listener_with_confirmation(
        self,
        info: strawberry.Info,
        timeout: Optional[float] = None,
        group: Optional[str] = None,
    ) -> AsyncGenerator[Union[str, None], None]:
        async with info.context["request"].listen_to_channel(
            type="test.message",
            timeout=timeout,
            groups=[group] if group is not None else [],
        ) as cm:
            yield None
            yield info.context["request"].channel_name
            async for message in cm:
                yield message["text"]

    @strawberry.subscription
    async def connection_params(
        self, info: strawberry.Info
    ) -> AsyncGenerator[strawberry.scalars.JSON, None]:
        yield info.context["connection_params"]

    @strawberry.subscription
    async def long_finalizer(
        self, info: strawberry.Info, delay: float = 0
    ) -> AsyncGenerator[str, None]:
        try:
            for _i in range(100):
                yield "hello"
                await asyncio.sleep(0.01)
        finally:
            await asyncio.sleep(delay)


class Schema(strawberry.Schema):
    def process_errors(
        self, errors: list, execution_context: Optional[ExecutionContext] = None
    ) -> None:
        import traceback

        traceback.print_stack()
        return super().process_errors(errors, execution_context)


schema = Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[MyExtension],
)
