import json
from typing import Any, Dict, Generic, List, Mapping, Optional, Union
from typing_extensions import Protocol

from strawberry.http import GraphQLHTTPResponse
from strawberry.http.types import HTTPMethod

from .exceptions import HTTPException
from .typevars import Request


class BaseRequestProtocol(Protocol):
    @property
    def query_params(self) -> Mapping[str, Optional[Union[str, List[str]]]]:
        ...

    @property
    def method(self) -> HTTPMethod:
        ...

    @property
    def headers(self) -> Mapping[str, str]:
        ...


class BaseView(Generic[Request]):
    def should_render_graphiql(self, request: BaseRequestProtocol) -> bool:
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

    def parse_json(self, data: Union[str, bytes]) -> Dict[str, str]:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e

    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return json.dumps(response_data)

    def parse_query_params(
        self, params: Mapping[str, Optional[Union[str, List[str]]]]
    ) -> Dict[str, Any]:
        params = dict(params)

        if "variables" in params:
            variables = params["variables"]

            if isinstance(variables, list):
                variables = variables[0]

            if variables:
                params["variables"] = json.loads(variables)

        return params
