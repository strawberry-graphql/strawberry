import json
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import Any, Generic
from typing_extensions import Protocol

from cross_web import HTTPException

from strawberry.http import GraphQLRequestData, GraphQLRequestProtocol
from strawberry.http.ides import GraphQL_IDE, get_graphql_ide_html
from strawberry.http.types import HTTPMethod, QueryParams
from strawberry.schema.base import BaseSchema
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    MULTIPART_SUBSCRIPTION_PROTOCOL,
)

from .streaming import HTTPStreamTransport, MultipartSubscriptionTransport, SSETransport
from .typevars import Request


class BaseRequestProtocol(Protocol):
    @property
    def query_params(self) -> Mapping[str, str | list[str] | None]: ...

    @property
    def method(self) -> HTTPMethod: ...

    @property
    def headers(self) -> Mapping[str, str]: ...


class BaseView(Generic[Request]):
    graphql_ide: GraphQL_IDE | None
    multipart_uploads_enabled: bool = False
    protocols: Sequence[str] = ()
    schema: BaseSchema
    stream_transport_classes_by_protocol: Mapping[str, type[HTTPStreamTransport]] = {
        MULTIPART_SUBSCRIPTION_PROTOCOL: MultipartSubscriptionTransport,
        GRAPHQL_SSE_PROTOCOL: SSETransport,
    }

    def should_render_graphql_ide(self, request: BaseRequestProtocol) -> bool:
        return (
            request.method == "GET"
            and request.query_params.get("query") is None
            and any(
                supported_header in request.headers.get("accept", "")
                for supported_header in ("text/html", "*/*")
            )
        )

    def is_request_allowed(self, request: BaseRequestProtocol) -> bool:
        return request.method in ("GET", "POST")

    def parse_json(self, data: str | bytes) -> Any:
        try:
            return self.decode_json(data)
        except json.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e

    def decode_json(self, data: str | bytes) -> object:
        return json.loads(data)

    def encode_json(self, data: object) -> str | bytes:
        return json.dumps(data)

    def parse_query_params(self, params: QueryParams) -> dict[str, Any]:
        params = dict(params)

        if "variables" in params:
            variables = params["variables"]

            if variables:
                params["variables"] = self.parse_json(variables)

        if "extensions" in params:
            extensions = params["extensions"]

            if extensions:
                params["extensions"] = self.parse_json(extensions)

        return params

    @property
    def graphql_ide_html(self) -> str:
        return get_graphql_ide_html(graphql_ide=self.graphql_ide)

    @cached_property
    def _stream_transport_map(self) -> dict[str, HTTPStreamTransport]:
        return {
            transport_class.protocol: transport_class()
            for protocol in self.protocols
            if (
                transport_class := self.stream_transport_classes_by_protocol.get(
                    protocol
                )
            )
        }

    def _get_stream_transport(self, protocol: str) -> HTTPStreamTransport | None:
        return self._stream_transport_map.get(protocol)

    def _get_stream_transport_from_headers(
        self, headers: Mapping[str, str]
    ) -> HTTPStreamTransport | None:
        accept = next(
            (value for key, value in headers.items() if key.lower() == "accept"),
            "",
        )

        return next(
            (
                transport
                for transport in self._stream_transport_map.values()
                if transport.accepts(accept)
            ),
            None,
        )

    def _get_stream_transport_from_content_type(
        self, content_type: str, params: dict[str, str]
    ) -> HTTPStreamTransport | None:
        return next(
            (
                transport
                for transport in self._stream_transport_map.values()
                if transport.accepts_content_type(content_type, params)
            ),
            None,
        )

    def _validate_batch_request(
        self, request_data: list[GraphQLRequestData], protocol: GraphQLRequestProtocol
    ) -> None:
        if self.schema.config.batching_config is None:
            raise HTTPException(400, "Batching is not enabled")

        if transport := self._get_stream_transport(protocol):
            raise HTTPException(400, transport.batching_error)

        if len(request_data) > self.schema.config.batching_config["max_operations"]:
            raise HTTPException(400, "Too many operations")


__all__ = ["BaseView"]
