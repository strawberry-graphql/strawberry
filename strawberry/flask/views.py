from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Tuple, Union

from flask import Request, Response, render_template_string, request
from flask.views import View
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.sync_base_view import (
    BaseSyncHTTPView,
    Context,
    HTTPException,
    RootValue,
)
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema


class FlaskHTTPRequestAdapter:
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        return self.request.args.to_dict()

    @property
    def body(self) -> str:
        return self.request.data.decode()

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        return self.request.form

    @property
    def files(self) -> Mapping[str, Any]:
        return self.request.files

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type


class BaseGraphQLView:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get

    def render_graphiql(self, request: Request) -> Response:
        template = get_graphiql_html(False)

        return render_template_string(template)

    def _create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))

        return sub_response


class GraphQLView(
    BaseGraphQLView, BaseSyncHTTPView[Request, Response, Context, RootValue], View
):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = FlaskHTTPRequestAdapter

    def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}

    def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    def dispatch_request(self) -> ResponseReturnValue:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )


class AsyncFlaskHTTPRequestAdapter:
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> Dict[str, Union[str, List[str]]]:
        return self.request.args.to_dict()

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    async def get_body(self) -> str:
        return self.request.data.decode()

    async def get_form_data(self) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
        return self.request.form, self.request.files


class AsyncGraphQLView(
    BaseGraphQLView, AsyncBaseHTTPView[Request, Response, Context, RootValue], View
):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = AsyncFlaskHTTPRequestAdapter

    async def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}

    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    async def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    async def dispatch_request(self) -> ResponseReturnValue:
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )
