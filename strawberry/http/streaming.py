from __future__ import annotations

import abc
from collections.abc import AsyncGenerator, Callable, Mapping
from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from strawberry.http import GraphQLHTTPResponse

from .parse_content_type import parse_content_type

JSONEncoder = Callable[[object], str]

MULTIPART_SUBSCRIPTION_BOUNDARY = "graphql"
MULTIPART_SUBSCRIPTION_HEARTBEAT_INTERVAL = 5
MULTIPART_INCREMENTAL_BOUNDARY = "-"
HTTPStreamProtocol = Literal["multipart-subscription"]
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
    protocol: ClassVar[HTTPStreamProtocol]
    batching_error: ClassVar[str]
    sync_not_supported_error: ClassVar[str] = (
        "Streaming responses are not supported in sync mode"
    )
    heartbeat_interval: ClassVar[float]
    send_initial_heartbeat: ClassVar[bool]

    @property
    @abc.abstractmethod
    def headers(self) -> Mapping[str, str]: ...

    @abc.abstractmethod
    def accepts(self, accept: str) -> bool: ...

    def accepts_content_type(self, content_type: str, params: dict[str, str]) -> bool:
        return False

    @abc.abstractmethod
    def encode_next(
        self, response: GraphQLHTTPResponse, encode_json: JSONEncoder
    ) -> str: ...

    @abc.abstractmethod
    def encode_complete(self) -> str: ...

    @abc.abstractmethod
    def heartbeat_message(self, encode_json: JSONEncoder) -> str: ...


class MultipartSubscriptionTransport(MultipartTransport, HTTPStreamTransport):
    protocol: ClassVar[HTTPStreamProtocol] = "multipart-subscription"
    batching_error: ClassVar[str] = (
        "Batching is not supported for multipart subscriptions"
    )
    sync_not_supported_error: ClassVar[str] = (
        "Multipart subscriptions are not supported in sync mode"
    )
    heartbeat_interval: ClassVar[float] = MULTIPART_SUBSCRIPTION_HEARTBEAT_INTERVAL
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

    def encode_next(
        self, response: GraphQLHTTPResponse, encode_json: JSONEncoder
    ) -> str:
        return self.encode_multipart_data({"payload": response}, encode_json)

    def encode_complete(self) -> str:
        return f"\r\n--{self.separator}--\r\n"

    def heartbeat_message(self, encode_json: JSONEncoder) -> str:
        return self.encode_multipart_data({}, encode_json)


__all__ = [
    "HTTPStreamTransport",
    "MultipartSubscriptionTransport",
    "MultipartTransport",
]
