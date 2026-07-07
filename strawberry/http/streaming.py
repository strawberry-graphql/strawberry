from __future__ import annotations

import abc
import asyncio
import contextlib
from collections.abc import AsyncGenerator, Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Any, ClassVar

from strawberry.types.graphql import OperationType

if TYPE_CHECKING:
    from strawberry.http import GraphQLHTTPResponse, GraphQLRequestProtocol

from .parse_content_type import parse_content_type

AsyncTextStream = Callable[[], AsyncGenerator[str, None]]
JSONEncoder = Callable[[object], str]

MULTIPART_SUBSCRIPTION_BOUNDARY = "graphql"
MULTIPART_SUBSCRIPTION_HEARTBEAT_INTERVAL = 5
MULTIPART_INCREMENTAL_BOUNDARY = "-"
SSE_HEARTBEAT_INTERVAL = 15
MultipartDataStream = Callable[[], AsyncGenerator[object, None]]
MultipartTextStream = Callable[[], AsyncGenerator[str, None]]


def _multipart_subscription_content_type(separator: str) -> str:
    return f"multipart/mixed;boundary={separator};subscriptionSpec=1.0,application/json"


MULTIPART_SUBSCRIPTION_CONTENT_TYPE = _multipart_subscription_content_type(
    MULTIPART_SUBSCRIPTION_BOUNDARY
)


class MultipartTransport:
    def __init__(self, separator: str = MULTIPART_INCREMENTAL_BOUNDARY) -> None:
        self.separator = separator

    @property
    def headers(self) -> Mapping[str, str]:
        return {"Content-Type": f'multipart/mixed; boundary="{self.separator}"'}

    def stream(
        self, data: MultipartDataStream, encode_json: JSONEncoder
    ) -> MultipartTextStream:
        async def stream() -> AsyncGenerator[str, None]:
            yield f"--{self.separator}"

            async for value in data():
                yield self.encode_multipart_data(value, encode_json)

            yield "--\r\n"

        return stream

    def encode_multipart_data(self, data: object, encode_json: JSONEncoder) -> str:
        encoded_data = encode_json(data)
        encoded_data_length = len(encoded_data.encode())

        return "".join(
            [
                "\r\n",
                "Content-Type: application/json; charset=utf-8\r\n",
                "Content-Length: " + str(encoded_data_length) + "\r\n",
                "\r\n",
                encoded_data,
                f"\r\n--{self.separator}",
            ]
        )


class HTTPStreamTransport(abc.ABC):
    protocol: ClassVar[GraphQLRequestProtocol]
    batching_error: ClassVar[str]
    sync_not_supported_error: ClassVar[str] = (
        "Streaming responses are not supported in sync mode"
    )
    heartbeat_interval: float
    send_initial_heartbeat: ClassVar[bool]

    @property
    @abc.abstractmethod
    def headers(self) -> Mapping[str, str]: ...

    @abc.abstractmethod
    def accepts(self, accept: str) -> bool: ...

    def accepts_content_type(self, content_type: str, params: dict[str, str]) -> bool:
        return False

    def allowed_operation_types(
        self, allowed_operation_types: set[OperationType]
    ) -> Iterable[OperationType]:
        return allowed_operation_types

    @abc.abstractmethod
    def encode_next(
        self, response: GraphQLHTTPResponse, encode_json: JSONEncoder
    ) -> str: ...

    @abc.abstractmethod
    def encode_complete(self) -> str: ...

    @abc.abstractmethod
    def heartbeat_message(self, encode_json: JSONEncoder) -> str: ...


class MultipartSubscriptionTransport(MultipartTransport, HTTPStreamTransport):
    protocol: ClassVar[GraphQLRequestProtocol] = "multipart-subscription"
    batching_error: ClassVar[str] = (
        "Batching is not supported for multipart subscriptions"
    )
    sync_not_supported_error: ClassVar[str] = (
        "Multipart subscriptions are not supported in sync mode"
    )
    heartbeat_interval: float = MULTIPART_SUBSCRIPTION_HEARTBEAT_INTERVAL
    send_initial_heartbeat: ClassVar[bool] = True

    def __init__(self, separator: str = MULTIPART_SUBSCRIPTION_BOUNDARY) -> None:
        super().__init__(separator)

    @property
    def headers(self) -> Mapping[str, str]:
        return {"Content-Type": _multipart_subscription_content_type(self.separator)}

    def accepts_content_type(self, content_type: str, params: dict[str, str]) -> bool:
        subscription_spec = params.get("subscriptionspec", "").strip("'\"")

        return (
            content_type == "multipart/mixed"
            and (
                "boundary" not in params
                or params["boundary"] == MULTIPART_SUBSCRIPTION_BOUNDARY
            )
            and subscription_spec.startswith("1.0")
        )

    def accepts(self, accept: str) -> bool:
        return self.accepts_content_type(*parse_content_type(accept))

    def allowed_operation_types(
        self, allowed_operation_types: set[OperationType]
    ) -> Iterable[OperationType]:
        return (OperationType.SUBSCRIPTION,)

    def encode_next(
        self, response: GraphQLHTTPResponse, encode_json: JSONEncoder
    ) -> str:
        return self.encode_multipart_data({"payload": response}, encode_json)

    def encode_complete(self) -> str:
        return f"\r\n--{self.separator}--\r\n"

    def heartbeat_message(self, encode_json: JSONEncoder) -> str:
        return self.encode_multipart_data({}, encode_json)


class SSETransport(HTTPStreamTransport):
    protocol: ClassVar[GraphQLRequestProtocol] = "sse"
    batching_error: ClassVar[str] = "Batching is not supported for SSE"
    headers: ClassVar[Mapping[str, str]] = {
        # SSE streams are identified by this media type.
        "Content-Type": "text/event-stream",
        # Avoid serving a cached response for a long-lived event stream, and
        # stop intermediaries from compressing or otherwise transforming it.
        "Cache-Control": "no-cache, no-transform",
        # Ask Nginx not to buffer SSE chunks so heartbeats flush promptly.
        "X-Accel-Buffering": "no",
    }
    heartbeat_interval: float = SSE_HEARTBEAT_INTERVAL
    send_initial_heartbeat: ClassVar[bool] = False

    def __init__(self, heartbeat_interval: float = SSE_HEARTBEAT_INTERVAL) -> None:
        self.heartbeat_interval = heartbeat_interval

    def accepts(self, accept: str) -> bool:
        return any(
            part.split(";", 1)[0].strip().lower() == "text/event-stream"
            for part in accept.split(",")
        )

    def encode_next(
        self, response: GraphQLHTTPResponse, encode_json: JSONEncoder
    ) -> str:
        return self.encode_event("next", encode_json(response))

    def encode_complete(self) -> str:
        return self.encode_event("complete")

    def heartbeat_message(self, encode_json: JSONEncoder) -> str:
        return self.encode_comment("ping")

    def encode_event(self, event: str, data: str | None = None) -> str:
        """Encode one SSE event from already-encoded ``data``.

        ``data`` must be a single line: SSE cannot carry a value with newlines in
        one field, so a multi-line ``encode_json`` output is rejected rather than
        silently reframed.
        """
        if data and ("\r" in data or "\n" in data):
            raise ValueError("SSE event data must not contain newlines")

        # Browsers discard SSE events without a data field, so always send one.
        return f"event: {event}\r\ndata: {data or ''}\r\n\r\n"

    def encode_comment(self, comment: str) -> str:
        return f": {comment}\r\n\r\n"


def merge_stream_with_heartbeat(
    stream: AsyncTextStream,
    heartbeat_message: Callable[[], str],
    interval: float,
    *,
    send_initial_heartbeat: bool,
) -> AsyncTextStream:
    """Add heartbeat messages to a stream to prevent connection timeouts.

    The source stream and heartbeat producer coordinate through a size-1 queue.
    That keeps backpressure natural and avoids accumulating heartbeats while
    data is active. The drain task sends an explicit completion message so a
    fast source stream cannot finish before the consumer has read its final
    chunk.
    """

    async def merged() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[tuple[bool, bool, Any]] = asyncio.Queue(maxsize=1)
        cancelling = False

        async def drain() -> None:
            try:
                async for item in stream():
                    await queue.put((False, False, item))
            except Exception as e:
                if not cancelling:
                    await queue.put((True, False, e))
                else:
                    raise

            await queue.put((False, True, None))

        async def heartbeat() -> None:
            if not send_initial_heartbeat:
                await asyncio.sleep(interval)

            while True:
                await queue.put((False, False, heartbeat_message()))
                await asyncio.sleep(interval)

        heartbeat_task = asyncio.create_task(heartbeat())
        task = asyncio.create_task(drain())

        async def cancel_tasks() -> None:
            nonlocal cancelling
            cancelling = True
            task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await task

            heartbeat_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

        try:
            while True:
                raised, done, data = await queue.get()

                if done:
                    break

                if raised:
                    await cancel_tasks()
                    raise data

                yield data
        finally:
            await cancel_tasks()

    return merged


__all__ = [
    "AsyncTextStream",
    "HTTPStreamTransport",
    "MultipartSubscriptionTransport",
    "MultipartTransport",
    "SSETransport",
    "merge_stream_with_heartbeat",
]
