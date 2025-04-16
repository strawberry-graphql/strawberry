import warnings
from collections.abc import AsyncGenerator, Mapping
from typing import TYPE_CHECKING, Callable, ClassVar, Optional, cast
from typing_extensions import TypeGuard

from quart import Request, Response, request
from quart.views import View
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue

if TYPE_CHECKING:
    from quart.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema


class QuartHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.args.to_dict()

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers  # type: ignore

    async def get_body(self) -> str:
        return (await self.request.data).decode()

    async def get_form_data(self) -> FormData:
        files = await self.request.files
        form = await self.request.form
        return FormData(files=files, form=form)


class GraphQLView(
    AsyncBaseHTTPView[
        Request, Response, Response, Request, Response, Context, RootValue
    ],
    View,
):
    methods: ClassVar[list[str]] = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = QuartHTTPRequestAdapter

    def __init__(
        self,
        schema: "BaseSchema",
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
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

    async def render_graphql_ide(self, request: Request) -> Response:
        return Response(self.graphql_ide_html)

    def create_response(
        self, response_data: "GraphQLHTTPResponse", sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))

        return sub_response

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

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncGenerator[str, None]],
        sub_response: Response,
        headers: dict[str, str],
    ) -> Response:
        return (
            stream(),
            sub_response.status_code,
            {  # type: ignore
                **sub_response.headers,
                **headers,
            },
        )

    def is_websocket_request(self, request: Request) -> TypeGuard[Request]:
        return False

    async def pick_websocket_subprotocol(self, request: Request) -> Optional[str]:
        raise NotImplementedError

    async def create_websocket_response(
        self, request: Request, subprotocol: Optional[str]
    ) -> Response:
        raise NotImplementedError


__all__ = ["GraphQLView"]
