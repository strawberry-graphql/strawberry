import contextlib
import json
import urllib.parse
from collections.abc import AsyncGenerator
from io import BytesIO
from typing import Any, Optional
from typing_extensions import Literal

from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from quart import Quart
from quart import Request as QuartRequest
from quart import Response as QuartResponse
from quart.datastructures import FileStorage
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.quart.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .asgi import AsgiWebSocketClient
from .base import (
    JSON,
    HttpClient,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
)


class GraphQLView(BaseGraphQLView[dict[str, object], object]):
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override", None)
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: QuartRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: QuartRequest, response: QuartResponse
    ) -> dict[str, object]:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: QuartRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class QuartAsgiAppAdapter:
    def __init__(self, app: Quart):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["asgi"] = scope.get("asgi", {})

        # Our WebSocket tests depend on WebSocket close reasons.
        # Quart only sends close reason if the ASGI spec version in the scope is => 2.3
        # https://github.com/pallets/quart/blob/b5593ca4c8c657564cdf2d35c9f0298fce63636b/src/quart/asgi.py#L347-L348
        scope["asgi"]["spec_version"] = "2.3"

        await self.app(scope, receive, send)  # type: ignore


class QuartHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = Quart(__name__)
        self.app.debug = True

        view = GraphQLView.as_view(
            "graphql_view",
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            keep_alive=False,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
        self.app.add_url_rule(
            "/graphql", view_func=view, methods=["GET"], websocket=True
        )

        self.client = TestClient(QuartAsgiAppAdapter(self.app))

    def create_app(self, **kwargs: Any) -> None:
        self.app = Quart(__name__)
        self.app.debug = True

        view = GraphQLView.as_view("graphql_view", schema=schema, **kwargs)

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
        self.app.add_url_rule(
            "/graphql", view_func=view, methods=["GET"], websocket=True
        )

        self.client = TestClient(QuartAsgiAppAdapter(self.app))

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: str,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        url = "/graphql"

        if method == "get":
            body_encoded = urllib.parse.urlencode(body or {})
            url = f"{url}?{body_encoded}"
        elif body:
            if files:
                kwargs["form"] = body
                kwargs["files"] = {
                    k: FileStorage(v, filename=k) for k, v in files.items()
                }
            else:
                kwargs["data"] = json.dumps(body)

        headers = self._get_headers(method=method, headers=headers, files=files)

        return await self.request(url, method, headers=headers, **kwargs)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        async with self.app.test_app() as test_app, self.app.app_context():
            client = test_app.test_client()
            response = await getattr(client, method)(url, headers=headers, **kwargs)

        return Response(
            status_code=response.status_code,
            data=(await response.data),
            headers=response.headers,
        )

    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        kwargs = {"headers": headers, "data": data, "json": json}
        return await self.request(
            url, "post", **{k: v for k, v in kwargs.items() if v is not None}
        )

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        with self.client.websocket_connect(url, protocols) as ws:
            yield AsgiWebSocketClient(ws)
