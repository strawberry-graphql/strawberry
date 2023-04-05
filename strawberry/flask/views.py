from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Union, cast

from flask import Request, Response, render_template_string, request
from flask.views import View
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.sync_base_view import (
    SyncBaseHTTPView,
    SyncHTTPRequestAdapter,
)
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema


class FlaskHTTPRequestAdapter(SyncHTTPRequestAdapter):
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> Mapping[str, Union[str, Optional[List[str]]]]:
        return self.request.args.to_dict()

    @property
    def body(self) -> Union[str, bytes]:
        return self.request.data.decode()

    @property
    def method(self) -> HTTPMethod:
        return cast(HTTPMethod, self.request.method.upper())

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

        return render_template_string(template)  # type: ignore

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))  # type: ignore

        return sub_response


class GraphQLView(
    BaseGraphQLView,
    SyncBaseHTTPView[Request, Response, Response, Context, RootValue],
    View,
):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = FlaskHTTPRequestAdapter

    def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}  # type: ignore

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


class AsyncFlaskHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.args.to_dict()

    @property
    def method(self) -> HTTPMethod:
        return cast(HTTPMethod, self.request.method.upper())

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    async def get_body(self) -> str:
        return self.request.data.decode()

    async def get_form_data(self) -> FormData:
        return FormData(
            files=self.request.files,
            form=self.request.form,
        )


class AsyncGraphQLView(
    BaseGraphQLView,
    AsyncBaseHTTPView[Request, Response, Response, Context, RootValue],
    View,
):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = AsyncFlaskHTTPRequestAdapter

    async def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    async def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    async def dispatch_request(self) -> ResponseReturnValue:  # type: ignore
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )
