import abc
import contextlib
import json
import logging
from collections.abc import AsyncGenerator, AsyncIterable, Mapping
from dataclasses import dataclass
from functools import cached_property
from io import BytesIO
from typing import Any, Callable, Optional, Union
from typing_extensions import Literal

from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    Message as GraphQLTransportWSMessage,
)
from strawberry.subscriptions.protocols.graphql_ws.handlers import BaseGraphQLWSHandler
from strawberry.subscriptions.protocols.graphql_ws.types import OperationMessage
from strawberry.types import ExecutionResult

logger = logging.getLogger("strawberry.test.http_client")

JSON = dict[str, object]
ResultOverrideFunction = Optional[Callable[[ExecutionResult], GraphQLHTTPResponse]]


@dataclass
class Response:
    status_code: int
    data: Union[bytes, AsyncIterable[bytes]]

    def __init__(
        self,
        status_code: int,
        data: Union[bytes, AsyncIterable[bytes]],
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.data = data
        self._headers = headers or {}

    @cached_property
    def headers(self) -> Mapping[str, str]:
        return {k.lower(): v for k, v in self._headers.items()}

    @property
    def is_multipart(self) -> bool:
        return self.headers.get("content-type", "").startswith("multipart/mixed")

    @property
    def text(self) -> str:
        assert isinstance(self.data, bytes)
        return self.data.decode()

    @property
    def json(self) -> JSON:
        assert isinstance(self.data, bytes)
        return json.loads(self.data)

    async def streaming_json(self) -> AsyncIterable[JSON]:
        if not self.is_multipart:
            raise ValueError("Streaming not supported")

        def parse_chunk(text: str) -> Union[JSON, None]:
            # TODO: better parsing? :)
            with contextlib.suppress(json.JSONDecodeError):
                return json.loads(text)

        if isinstance(self.data, AsyncIterable):
            chunks = self.data

            async for chunk in chunks:
                lines = chunk.decode("utf-8").split("\r\n")

                for text in lines:
                    if data := parse_chunk(text):
                        yield data
        else:
            # TODO: we do this because httpx doesn't support streaming
            # it would be nice to fix httpx instead of doing this,
            # but we might have the same issue in other clients too
            # TODO: better message
            logger.warning("Didn't receive a stream, parsing it sync")

            chunks = self.data.decode("utf-8").split("\r\n")

            for chunk in chunks:
                if data := parse_chunk(chunk):
                    yield data


class HttpClient(abc.ABC):
    @abc.abstractmethod
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ): ...

    @abc.abstractmethod
    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: str,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response: ...

    @abc.abstractmethod
    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
    ) -> Response: ...

    @abc.abstractmethod
    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> Response: ...

    @abc.abstractmethod
    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response: ...

    async def query(
        self,
        query: str,
        method: Literal["get", "post"] = "post",
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        return await self._graphql_request(
            method, query=query, headers=headers, variables=variables, files=files
        )

    def _get_headers(
        self,
        method: Literal["get", "post"],
        headers: Optional[dict[str, str]],
        files: Optional[dict[str, BytesIO]],
    ) -> dict[str, str]:
        additional_headers = {}
        headers = headers or {}

        # TODO: fix case sensitivity
        content_type = headers.get("content-type")

        if not content_type and method == "post" and not files:
            content_type = "application/json"

        additional_headers = {"Content-Type": content_type} if content_type else {}

        return {**additional_headers, **headers}

    def _build_body(
        self,
        query: Optional[str] = None,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        method: Literal["get", "post"] = "post",
    ) -> Optional[dict[str, object]]:
        if query is None:
            assert files is None
            assert variables is None

            return None

        body: dict[str, object] = {"query": query}

        if variables:
            body["variables"] = variables

        if files:
            assert variables is not None

            file_map = self._build_multipart_file_map(variables, files)

            body = {
                "operations": json.dumps(body),
                "map": json.dumps(file_map),
            }

        if method == "get" and variables:
            body["variables"] = json.dumps(variables)

        return body

    @staticmethod
    def _build_multipart_file_map(
        variables: dict[str, object], files: dict[str, BytesIO]
    ) -> dict[str, list[str]]:
        # TODO: remove code duplication

        files_map: dict[str, list[str]] = {}
        for key, values in variables.items():
            if isinstance(values, dict):
                folder_key = next(iter(values.keys()))
                key += f".{folder_key}"  # noqa: PLW2901
                # the list of file is inside the folder keyword
                values = values[folder_key]  # noqa: PLW2901

            # If the variable is an array of files we must number the keys
            if isinstance(values, list):
                # copying `files` as when we map a file we must discard from the dict
                _kwargs = files.copy()
                for index, _ in enumerate(values):
                    k = next(iter(_kwargs.keys()))
                    _kwargs.pop(k)
                    files_map.setdefault(k, [])
                    files_map[k].append(f"variables.{key}.{index}")
            else:
                files_map[key] = [f"variables.{key}"]

        return files_map

    def create_app(self, **kwargs: Any) -> None:
        """For use by websocket tests."""
        raise NotImplementedError

    def ws_connect(
        self,
        url: str,
        *,
        protocols: list[str],
    ) -> contextlib.AbstractAsyncContextManager["WebSocketClient"]:
        raise NotImplementedError


@dataclass
class Message:
    type: Any
    data: Any
    extra: Optional[str] = None

    def json(self) -> Any:
        return json.loads(self.data)


class WebSocketClient(abc.ABC):
    def name(self) -> str:
        return ""

    @abc.abstractmethod
    async def send_text(self, payload: str) -> None: ...

    @abc.abstractmethod
    async def send_json(self, payload: Mapping[str, object]) -> None: ...

    @abc.abstractmethod
    async def send_bytes(self, payload: bytes) -> None: ...

    @abc.abstractmethod
    async def receive(self, timeout: Optional[float] = None) -> Message: ...

    @abc.abstractmethod
    async def receive_json(self, timeout: Optional[float] = None) -> Any: ...

    @abc.abstractmethod
    async def close(self) -> None: ...

    @property
    @abc.abstractmethod
    def accepted_subprotocol(self) -> Optional[str]: ...

    @property
    @abc.abstractmethod
    def closed(self) -> bool: ...

    @property
    @abc.abstractmethod
    def close_code(self) -> int: ...

    @property
    @abc.abstractmethod
    def close_reason(self) -> Optional[str]: ...

    async def __aiter__(self) -> AsyncGenerator[Message, None]:
        while not self.closed:
            yield await self.receive()

    async def send_message(self, message: GraphQLTransportWSMessage) -> None:
        await self.send_json(message)

    async def send_legacy_message(self, message: OperationMessage) -> None:
        await self.send_json(message)


class DebuggableGraphQLTransportWSHandler(
    BaseGraphQLTransportWSHandler[dict[str, object], object]
):
    def on_init(self) -> None:
        """This method can be patched by unit tests to get the instance of the
        transport handler when it is initialized.
        """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.original_context = kwargs.get("context", {})
        DebuggableGraphQLTransportWSHandler.on_init(self)

    def get_tasks(self) -> list:
        return [op.task for op in self.operations.values()]

    @property
    def context(self):
        self.original_context["ws"] = self.websocket
        self.original_context["get_tasks"] = self.get_tasks
        self.original_context["connectionInitTimeoutTask"] = (
            self.connection_init_timeout_task
        )
        return self.original_context

    @context.setter
    def context(self, value):
        self.original_context = value


class DebuggableGraphQLWSHandler(BaseGraphQLWSHandler[dict[str, object], object]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.original_context = kwargs.get("context", {})

    def get_tasks(self) -> list:
        return list(self.tasks.values())

    @property
    def context(self):
        self.original_context["ws"] = self.websocket
        self.original_context["get_tasks"] = self.get_tasks
        self.original_context["connectionInitTimeoutTask"] = None
        return self.original_context

    @context.setter
    def context(self, value):
        self.original_context = value
