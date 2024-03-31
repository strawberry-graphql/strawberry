import asyncio
import contextlib
import inspect
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

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


class ConditionalFailPermission(BasePermission):
    @property
    def message(self):
        return f"failed after sleep {self.sleep}"

    async def has_permission(self, source, info, **kwargs: Any) -> bool:
        self.sleep = kwargs.get("sleep", None)
        self.fail = kwargs.get("fail", True)
        if self.sleep is not None:
            await asyncio.sleep(kwargs["sleep"])
        return not self.fail


class MyExtension(SchemaExtension):
    # a counter to keep track of how many operations are active
    active_counter = 0

    def get_results(self) -> Dict[str, str]:
        return {"example": "example"}

    def resolve(self, _next, root, info: Info, *args: Any, **kwargs: Any):
        self.active_counter += 1
        try:
            self.resolve_called()
            return _next(root, info, *args, **kwargs)
        finally:
            self.active_counter -= 1

    def resolve_called(self):
        pass

    def lifecycle_called(self, event, phase):
        pass

    def on_operation(self):
        self.lifecycle_called("operation", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("operation", "after")
        self.active_counter -= 1

    def on_validate(self):
        self.lifecycle_called("validate", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("validate", "after")
        self.active_counter -= 1

    def on_parse(self):
        self.lifecycle_called("parse", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("parse", "after")
        self.active_counter -= 1

    def on_execute(self):
        self.lifecycle_called("execute", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("execute", "after")
        self.active_counter -= 1


class MyAsyncExtension(SchemaExtension):
    # a counter to keep track of how many operations are active
    active_counter = 0

    def get_results(self) -> Dict[str, str]:
        return {"example": "example"}

    async def resolve(self, _next, root, info: Info, *args: Any, **kwargs: Any):
        self.resolve_called()
        self.active_counter += 1
        try:
            result = _next(root, info, *args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        finally:
            self.active_counter -= 1

    def resolve_called(self):
        pass

    def lifecycle_called(self, event, phase):
        pass

    async def on_operation(self):
        self.lifecycle_called("operation", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("operation", "after")
        self.active_counter -= 1

    async def on_validate(self):
        self.lifecycle_called("validate", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("validate", "after")
        self.active_counter -= 1

    async def on_parse(self):
        self.lifecycle_called("parse", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("parse", "after")
        self.active_counter -= 1

    async def on_execute(self):
        self.lifecycle_called("execute", "before")
        self.active_counter += 1
        yield
        self.lifecycle_called("execute", "after")
        self.active_counter -= 1


def _read_file(text_file: Upload) -> str:
    with contextlib.suppress(ModuleNotFoundError):
        from starlette.datastructures import UploadFile

        # allow to keep this function synchronous, starlette's files have
        # async methods for reading
        if isinstance(text_file, UploadFile):
            text_file = text_file.file._file  # type: ignore

    with contextlib.suppress(Exception):
        from starlite import UploadFile as StarliteUploadFile

        if isinstance(text_file, StarliteUploadFile):
            text_file = text_file.file  # type: ignore

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
    files: List[Upload]


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

    @strawberry.field(permission_classes=[ConditionalFailPermission])
    def conditional_fail(
        self, sleep: Optional[float] = None, fail: bool = False
    ) -> str:
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
    def read_files(self, files: List[Upload]) -> List[str]:
        return list(map(_read_file, files))

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> List[str]:
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
        await ws.send_json(PingMessage().as_dict())
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

        async for message in info.context["request"].channel_listen(
            type="test.message",
            timeout=timeout,
            groups=[group] if group is not None else [],
        ):
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
    ) -> AsyncGenerator[str, None]:
        yield info.context["connection_params"]["strawberry"]

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

    @strawberry.subscription(permission_classes=[ConditionalFailPermission])
    async def conditional_fail(
        self, sleep: Optional[float] = None, fail: bool = False
    ) -> AsyncGenerator[str, None]:
        yield "Hey"


class Schema(strawberry.Schema):
    def process_errors(
        self, errors: List, execution_context: Optional[ExecutionContext] = None
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

async_schema = Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[MyAsyncExtension],
)
