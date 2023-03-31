from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Union

from chalice.app import Request, Response
from strawberry.http.base_view import BaseHTTPView, Context, HTTPException, RootValue
from strawberry.http.temporal_response import TemporalResponse
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from chalice.app import Request
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema import BaseSchema


class ChaliceHTTPRequestAdapter:
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        return self.request.query_params or {}

    @property
    def body(self) -> str:
        return self.request.raw_body

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        raise NotImplementedError

    @property
    def files(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @property
    def content_type(self) -> Optional[str]:
        return self.request.headers.get("Content-Type", None)


class GraphQLView(BaseHTTPView[Request, Response, Context, RootValue]):
    allow_queries_via_get: bool = True
    request_adapter_class = ChaliceHTTPRequestAdapter

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
    ):
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.schema = schema

    def get_root_value(self, request: Request) -> Optional[object]:
        return None

    def render_graphiql(self, request: Request) -> Response:
        """
        Returns a string containing the html for the graphiql webpage. It also caches
        the result using lru cache.
        This saves loading from disk each time it is invoked.

        Returns:
            The GraphiQL html page as a string
        """
        return get_graphiql_html(subscription_enabled=False)

    def get_sub_response(self, request: Request) -> Response:
        return TemporalResponse()

    @staticmethod
    def error_response(
        message: str,
        error_code: str,
        http_status_code: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        A wrapper for error responses
        Returns:
        An errors response
        """
        body = {"Code": error_code, "Message": message}

        return Response(body=body, status_code=http_status_code, headers=headers)

    def get_context(self, request: Request, response: TemporalResponse) -> Context:
        return {"request": request, "response": response}

    def _create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        status_code = 200

        if sub_response.status_code != 200:
            status_code = sub_response.status_code

        return Response(body=self.encode_json(response_data), status_code=status_code)

    def execute_request(self, request: Request) -> Response:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return self.error_response(
                # TODO: map error codes?
                error_code=e.status_code,
                message=e.reason,
                http_status_code=e.status_code,
            )
