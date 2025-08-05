from __future__ import annotations

import warnings
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Optional,
    Union,
)
from typing_extensions import TypeGuard

from lia import AsyncFlaskHTTPRequestAdapter, FlaskHTTPRequestAdapter, HTTPException

from flask import Request, Response, render_template_string, request
from flask.views import View
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.sync_base_view import SyncBaseHTTPView
from strawberry.http.typevars import Context, RootValue

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema.base import BaseSchema


class BaseGraphQLView:
    graphql_ide: Optional[GraphQL_IDE]

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    def create_response(
        self,
        response_data: Union[GraphQLHTTPResponse, list[GraphQLHTTPResponse]],
        sub_response: Response,
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))  # type: ignore

        return sub_response


class GraphQLView(
    BaseGraphQLView,
    SyncBaseHTTPView[Request, Response, Response, Context, RootValue],
    View,
):
    methods: ClassVar[list[str]] = ["GET", "POST"]
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

    def render_graphql_ide(self, request: Request) -> Response:
        return render_template_string(self.graphql_ide_html)  # type: ignore


class AsyncGraphQLView(
    BaseGraphQLView,
    AsyncBaseHTTPView[
        Request, Response, Response, Request, Response, Context, RootValue
    ],
    View,
):
    methods: ClassVar[list[str]] = ["GET", "POST"]
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

    async def render_graphql_ide(self, request: Request) -> Response:
        content = render_template_string(self.graphql_ide_html)
        return Response(content, status=200, content_type="text/html")

    def is_websocket_request(self, request: Request) -> TypeGuard[Request]:
        return False

    async def pick_websocket_subprotocol(self, request: Request) -> Optional[str]:
        raise NotImplementedError

    async def create_websocket_response(
        self, request: Request, subprotocol: Optional[str]
    ) -> Response:
        raise NotImplementedError


__all__ = [
    "AsyncGraphQLView",
    "GraphQLView",
]
