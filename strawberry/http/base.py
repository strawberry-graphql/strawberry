import json
from typing import Any, Dict, Generic, List, Mapping, Union
from typing_extensions import Protocol

from strawberry.http import GraphQLHTTPResponse

from .exceptions import HTTPException
from .typevars import Request


class BaseRequestProtocol(Protocol):
    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        ...

    @property
    def method(self) -> str:
        ...

    @property
    def headers(self) -> Mapping[str, str]:
        ...


class BaseView(Generic[Request]):
    def should_render_graphiql(self, request: BaseRequestProtocol) -> bool:
        return (
            request.method.lower() == "get"
            and request.query_params.get("query") is None
            and any(
                supported_header in request.headers.get("accept", "")
                for supported_header in ("text/html", "*/*")
            )
        )

    def is_request_allowed(self, request: BaseRequestProtocol) -> bool:
        return request.method.lower() in ("get", "post")

    def parse_json(self, data: Union[str, bytes]) -> Dict[str, str]:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise HTTPException(400, "Unable to parse request body as JSON") from e

    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return json.dumps(response_data)

    def parse_query_params(
        self, params: Dict[str, Union[str, List[str]]]
    ) -> Dict[str, Any]:
        if "variables" in params:
            variables = params["variables"]

            if isinstance(variables, list):
                variables = variables[0]

            params["variables"] = json.loads(variables)

        return params
