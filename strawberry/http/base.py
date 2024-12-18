import json
from collections.abc import Mapping
from typing import Any, Generic, Optional, Union
from typing_extensions import Protocol

from strawberry.http.ides import GraphQL_IDE, get_graphql_ide_html
from strawberry.http.types import HTTPMethod, QueryParams

from .exceptions import HTTPException
from .typevars import Request


class BaseRequestProtocol(Protocol):
    @property
    def query_params(self) -> Mapping[str, Optional[Union[str, list[str]]]]: ...

    @property
    def method(self) -> HTTPMethod: ...

    @property
    def headers(self) -> Mapping[str, str]: ...


class BaseView(Generic[Request]):
    graphql_ide: Optional[GraphQL_IDE]
    multipart_uploads_enabled: bool = False

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

    def parse_json(self, data: Union[str, bytes]) -> Any:
        try:
            return self.decode_json(data)
        except json.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e

    def decode_json(self, data: Union[str, bytes]) -> object:
        return json.loads(data)

    def encode_json(self, data: object) -> str:
        return json.dumps(data)

    def parse_query_params(self, params: QueryParams) -> dict[str, Any]:
        params = dict(params)

        if "variables" in params:
            variables = params["variables"]

            if variables:
                params["variables"] = self.parse_json(variables)

        return params

    @property
    def graphql_ide_html(self) -> str:
        return get_graphql_ide_html(graphql_ide=self.graphql_ide)

    def _is_multipart_subscriptions(
        self, content_type: str, params: dict[str, str]
    ) -> bool:
        if content_type != "multipart/mixed":
            return False

        if params.get("boundary") != "graphql":
            return False

        return params.get("subscriptionspec", "").startswith("1.0")


__all__ = ["BaseView"]
