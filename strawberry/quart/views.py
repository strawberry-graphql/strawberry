from collections.abc import Mapping
from typing import TYPE_CHECKING, Optional, cast

from quart import Request, Response, request
from quart.views import View
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from quart.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema


class BaseGraphQLView:
    def __init__(
        self,
        schema: "BaseSchema",
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get

    def render_graphiql(self, request: Request) -> Response:
        template = get_graphiql_html(False)
        return Response(template)

    def create_response(
        self, response_data: "GraphQLHTTPResponse", sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))  # type: ignore
        return sub_response


class QuartHTTPRequestAdapter(AsyncHTTPRequestAdapter):
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
        return (await self.request.data).decode()

    async def get_form_data(self) -> FormData:
        files = await self.request.files
        form = await self.request.form
        return FormData(files=files, form=form)


class GraphQLView(
    BaseGraphQLView,
    AsyncBaseHTTPView[Request, Response, Response, Context, RootValue],
    View,
):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = QuartHTTPRequestAdapter

    async def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    async def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    async def dispatch_request(self) -> "ResponseReturnValue":  # type: ignore
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )
